use axum::{
    http::{HeaderMap, StatusCode},
    response::{IntoResponse, Response},
    Json,
};
use jsonwebtoken::{decode, encode, Algorithm, DecodingKey, EncodingKey, Header, Validation};
use loco_rs::app::AppContext;
use sea_orm::DbErr;
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};

pub type ApiResult = Result<Response, ApiError>;

#[derive(Debug)]
pub struct ApiError(pub StatusCode, pub Value);

impl IntoResponse for ApiError {
    fn into_response(self) -> Response {
        respond(self.0, self.1)
    }
}

impl From<DbErr> for ApiError {
    fn from(error: DbErr) -> Self {
        tracing::error!(%error, "database error");
        fail(StatusCode::INTERNAL_SERVER_ERROR, "server", "error")
    }
}

pub fn respond(status: StatusCode, body: Value) -> Response {
    let mut response = (status, Json(body)).into_response();
    response.headers_mut().insert(
        "x-content-type-options",
        "nosniff".parse().expect("static header"),
    );
    response
}

pub fn empty() -> Response {
    StatusCode::NO_CONTENT.into_response()
}

pub fn fail(status: StatusCode, field: &str, message: &str) -> ApiError {
    let mut errors = serde_json::Map::new();
    errors.insert(field.to_owned(), json!([message]));
    ApiError(status, json!({"errors":errors}))
}

pub fn invalid(field: &str) -> ApiError {
    fail(StatusCode::UNPROCESSABLE_ENTITY, field, "is invalid")
}
pub fn blank(field: &str) -> ApiError {
    fail(StatusCode::UNPROCESSABLE_ENTITY, field, "can't be blank")
}
pub fn missing(field: &str) -> ApiError {
    fail(StatusCode::NOT_FOUND, field, "not found")
}
pub fn forbidden(field: &str) -> ApiError {
    fail(StatusCode::FORBIDDEN, field, "forbidden")
}

pub fn object<'a>(body: &'a Value, key: &str) -> Result<&'a Value, ApiError> {
    body.get(key)
        .filter(|v| v.is_object())
        .ok_or_else(|| invalid(key))
}

pub fn required<'a>(body: &'a Value, field: &str) -> Result<&'a str, ApiError> {
    body.get(field)
        .and_then(Value::as_str)
        .filter(|s| !s.trim().is_empty())
        .ok_or_else(|| blank(field))
}

pub fn optional_text(body: &Value, field: &str) -> Result<Option<String>, ApiError> {
    match body.get(field) {
        None => Ok(None),
        Some(Value::String(s)) if !s.trim().is_empty() => Ok(Some(s.clone())),
        _ => Err(blank(field)),
    }
}

#[derive(Serialize, Deserialize, Clone)]
struct Claims {
    sub: i64,
    exp: usize,
}

pub fn token(ctx: &AppContext, id: i64) -> String {
    let secret = &ctx.config.get_jwt_config().expect("configured jwt").secret;
    let claims = Claims {
        sub: id,
        exp: (chrono::Utc::now().timestamp() + 604800) as usize,
    };
    encode(
        &Header::new(Algorithm::HS256),
        &claims,
        &EncodingKey::from_secret(secret.as_bytes()),
    )
    .expect("jwt encoding")
}

pub fn viewer(ctx: &AppContext, headers: &HeaderMap) -> Option<i64> {
    let value = headers
        .get("authorization")?
        .to_str()
        .ok()?
        .strip_prefix("Token ")?;
    let secret = &ctx.config.get_jwt_config().ok()?.secret;
    decode::<Claims>(
        value,
        &DecodingKey::from_secret(secret.as_bytes()),
        &Validation::new(Algorithm::HS256),
    )
    .ok()
    .map(|data| data.claims.sub)
}

pub fn required_viewer(ctx: &AppContext, headers: &HeaderMap) -> Result<i64, ApiError> {
    viewer(ctx, headers).ok_or_else(|| fail(StatusCode::UNAUTHORIZED, "token", "is missing"))
}

pub fn id(value: &Value) -> i64 {
    value["id"].as_i64().unwrap_or_default()
}

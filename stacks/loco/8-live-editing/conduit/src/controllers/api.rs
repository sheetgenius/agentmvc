use axum::{
    extract::FromRequestParts,
    http::{request::Parts, StatusCode},
    response::{IntoResponse, Response},
    Json,
};
use loco_rs::{app::AppContext, auth::jwt};
use sea_orm::DbErr;
use serde::Serialize;
use serde_json::json;

use crate::models::users;

pub type ApiResult = std::result::Result<Response, ApiError>;

pub struct ApiError {
    status: StatusCode,
    field: &'static str,
    message: &'static str,
}

impl ApiError {
    pub fn new(status: StatusCode, field: &'static str, message: &'static str) -> Self {
        Self {
            status,
            field,
            message,
        }
    }
    pub fn blank(field: &'static str) -> Self {
        Self::new(StatusCode::UNPROCESSABLE_ENTITY, field, "can't be blank")
    }
    pub fn invalid(field: &'static str) -> Self {
        Self::new(StatusCode::UNPROCESSABLE_ENTITY, field, "is invalid")
    }
    pub fn taken(field: &'static str) -> Self {
        Self::new(StatusCode::CONFLICT, field, "has already been taken")
    }
    pub fn missing(field: &'static str) -> Self {
        Self::new(StatusCode::NOT_FOUND, field, "not found")
    }
    pub fn forbidden(field: &'static str) -> Self {
        Self::new(StatusCode::FORBIDDEN, field, "forbidden")
    }
}

impl From<DbErr> for ApiError {
    fn from(_: DbErr) -> Self {
        Self::new(StatusCode::INTERNAL_SERVER_ERROR, "server", "error")
    }
}

impl From<loco_rs::model::ModelError> for ApiError {
    fn from(_: loco_rs::model::ModelError) -> Self {
        Self::new(StatusCode::INTERNAL_SERVER_ERROR, "server", "error")
    }
}

impl From<loco_rs::Error> for ApiError {
    fn from(_: loco_rs::Error) -> Self {
        Self::new(StatusCode::INTERNAL_SERVER_ERROR, "server", "error")
    }
}

impl IntoResponse for ApiError {
    fn into_response(self) -> Response {
        (
            self.status,
            Json(json!({"errors": {self.field: [self.message]}})),
        )
            .into_response()
    }
}

pub fn json_response<T: Serialize>(status: StatusCode, value: T) -> Response {
    (status, Json(value)).into_response()
}

pub fn required(value: &str, field: &'static str) -> std::result::Result<(), ApiError> {
    if value.trim().is_empty() {
        Err(ApiError::blank(field))
    } else {
        Ok(())
    }
}

pub struct Viewer(pub users::Model);
pub struct OptionalViewer(pub Option<users::Model>);

impl FromRequestParts<AppContext> for OptionalViewer {
    type Rejection = ApiError;

    async fn from_request_parts(
        parts: &mut Parts,
        ctx: &AppContext,
    ) -> std::result::Result<Self, Self::Rejection> {
        let Some(header) = parts.headers.get(axum::http::header::AUTHORIZATION) else {
            return Ok(Self(None));
        };
        let token = header
            .to_str()
            .ok()
            .and_then(|value| value.strip_prefix("Token "))
            .ok_or(ApiError::new(
                StatusCode::UNAUTHORIZED,
                "token",
                "is invalid",
            ))?;
        let config = ctx
            .config
            .get_jwt_config()
            .map_err(|_| ApiError::new(StatusCode::INTERNAL_SERVER_ERROR, "server", "error"))?;
        let claims = jwt::JWT::new(&config.secret)
            .validate(token)
            .map_err(|_| ApiError::new(StatusCode::UNAUTHORIZED, "token", "is invalid"))?;
        let user = users::Model::by_pid(&ctx.db, &claims.claims.pid).await?;
        Ok(Self(user))
    }
}

impl FromRequestParts<AppContext> for Viewer {
    type Rejection = ApiError;

    async fn from_request_parts(
        parts: &mut Parts,
        ctx: &AppContext,
    ) -> std::result::Result<Self, Self::Rejection> {
        let OptionalViewer(user) = OptionalViewer::from_request_parts(parts, ctx).await?;
        user.map(Self).ok_or(ApiError::new(
            StatusCode::UNAUTHORIZED,
            "token",
            "is missing",
        ))
    }
}

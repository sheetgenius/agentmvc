use axum::{
    extract::{Path, State},
    http::StatusCode,
};
use loco_rs::prelude::*;
use serde_json::json;

use crate::{
    controllers::api::{self, ApiError, ApiResult, Viewer},
    models::exports,
    views::realworld::ExportView,
    workers::export_articles::ExportArticlesWorker,
};

#[debug_handler]
async fn create(Viewer(user): Viewer, State(ctx): State<AppContext>) -> ApiResult {
    let export = exports::Model::create(&ctx.db, user.id).await?;
    ExportArticlesWorker::perform_later(&ctx, export.id).await?;
    Ok(api::json_response(
        StatusCode::ACCEPTED,
        json!({"export": ExportView::from(&export)}),
    ))
}

#[debug_handler]
async fn show(
    Path(id): Path<String>,
    Viewer(user): Viewer,
    State(ctx): State<AppContext>,
) -> ApiResult {
    let export = match id.parse::<i64>() {
        Ok(id) => exports::Model::for_user(&ctx.db, id, user.id).await?,
        Err(_) => None,
    }
    .ok_or(ApiError::missing("export"))?;
    Ok(api::json_response(
        StatusCode::OK,
        json!({"export": ExportView::from(&export)}),
    ))
}

pub fn routes() -> Routes {
    Routes::new()
        .prefix("/api")
        .add("/user/exports", post(create))
        .add("/user/exports/{id}", get(show))
}

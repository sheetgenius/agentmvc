use axum::{
    extract::{Path, State},
    http::StatusCode,
};
use loco_rs::prelude::*;
use serde_json::json;

use crate::{
    controllers::api::{self, ApiError, ApiResult, OptionalViewer, Viewer},
    models::{follows, users},
    views::realworld::ProfileView,
};

async fn profile(
    ctx: &AppContext,
    user: &users::Model,
    viewer: Option<&users::Model>,
) -> ApiResult {
    let profile = ProfileView::load(&ctx.db, user, viewer).await?;
    Ok(api::json_response(
        StatusCode::OK,
        json!({"profile": profile}),
    ))
}

#[debug_handler]
async fn show(
    Path(username): Path<String>,
    OptionalViewer(viewer): OptionalViewer,
    State(ctx): State<AppContext>,
) -> ApiResult {
    let user = users::Model::by_username(&ctx.db, &username)
        .await?
        .ok_or(ApiError::missing("profile"))?;
    profile(&ctx, &user, viewer.as_ref()).await
}

#[debug_handler]
async fn follow(
    Path(username): Path<String>,
    Viewer(viewer): Viewer,
    State(ctx): State<AppContext>,
) -> ApiResult {
    let user = users::Model::by_username(&ctx.db, &username)
        .await?
        .ok_or(ApiError::missing("profile"))?;
    follows::Model::set(&ctx.db, viewer.id, user.id, true).await?;
    profile(&ctx, &user, Some(&viewer)).await
}

#[debug_handler]
async fn unfollow(
    Path(username): Path<String>,
    Viewer(viewer): Viewer,
    State(ctx): State<AppContext>,
) -> ApiResult {
    let user = users::Model::by_username(&ctx.db, &username)
        .await?
        .ok_or(ApiError::missing("profile"))?;
    follows::Model::set(&ctx.db, viewer.id, user.id, false).await?;
    profile(&ctx, &user, Some(&viewer)).await
}

pub fn routes() -> Routes {
    Routes::new()
        .prefix("/api/profiles")
        .add("/{username}", get(show))
        .add("/{username}/follow", post(follow))
        .add("/{username}/follow", delete(unfollow))
}

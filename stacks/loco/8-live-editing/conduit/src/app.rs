use async_trait::async_trait;
use loco_rs::{
    app::{AppContext, Hooks},
    bgworker::{BackgroundWorker, Queue},
    boot::{create_app, BootResult, StartMode},
    config::Config,
    controller::AppRoutes,
    environment::Environment,
    task::Tasks,
    Result,
};
use migration::Migrator;
use std::path::Path;
use std::sync::Arc;

use crate::{controllers, models::live_rooms::Hub, workers::export_articles::ExportArticlesWorker};

pub struct App;

#[async_trait]
impl Hooks for App {
    fn app_name() -> &'static str {
        env!("CARGO_CRATE_NAME")
    }

    async fn boot(
        mode: StartMode,
        environment: &Environment,
        config: Config,
    ) -> Result<BootResult> {
        create_app::<Self, Migrator>(mode, environment, config).await
    }

    fn routes(_ctx: &AppContext) -> AppRoutes {
        AppRoutes::with_default_routes()
            .add_route(controllers::users::routes())
            .add_route(controllers::profiles::routes())
            .add_route(controllers::articles::routes())
            .add_route(controllers::comments::routes())
            .add_route(controllers::exports::routes())
            .add_route(controllers::shares::routes())
    }

    async fn after_context(ctx: AppContext) -> Result<AppContext> {
        ctx.shared_store.insert(Arc::new(Hub::default()));
        Ok(ctx)
    }

    async fn connect_workers(ctx: &AppContext, queue: &Queue) -> Result<()> {
        queue.register(ExportArticlesWorker::build(ctx)).await?;
        Ok(())
    }
    fn register_tasks(_tasks: &mut Tasks) {}
    async fn truncate(_ctx: &AppContext) -> Result<()> {
        Ok(())
    }
    async fn seed(_ctx: &AppContext, _base: &Path) -> Result<()> {
        Ok(())
    }
}

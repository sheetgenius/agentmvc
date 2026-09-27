use loco_rs::prelude::*;

use crate::models::exports;

pub struct ExportArticlesWorker {
    ctx: AppContext,
}

#[async_trait]
impl BackgroundWorker<i64> for ExportArticlesWorker {
    fn build(ctx: &AppContext) -> Self {
        Self { ctx: ctx.clone() }
    }

    async fn perform(&self, export_id: i64) -> Result<()> {
        exports::Model::complete(&self.ctx.db, export_id).await?;
        Ok(())
    }
}

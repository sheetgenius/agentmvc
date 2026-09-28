use crate::models::realworld as db;
use loco_rs::prelude::*;
use serde::{Deserialize, Serialize};

pub struct ExportWorker {
    ctx: AppContext,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct ExportArgs {
    pub id: String,
}

#[async_trait]
impl BackgroundWorker<ExportArgs> for ExportWorker {
    fn build(ctx: &AppContext) -> Self {
        Self { ctx: ctx.clone() }
    }
    async fn perform(&self, args: ExportArgs) -> Result<()> {
        let Some(export) = db::row(&self.ctx.db,"SELECT row_to_json(t)::text data FROM (SELECT user_id FROM rw_exports WHERE id=$1 AND status='pending') t",vec![args.id.clone().into()]).await? else { return Ok(()) };
        let snapshot =
            db::export_snapshot(&self.ctx.db, export["user_id"].as_i64().unwrap_or_default())
                .await?;
        db::exec(&self.ctx.db,"UPDATE rw_exports SET status='done',completed_at=now(),articles=$2::jsonb WHERE id=$1 AND status='pending'",vec![args.id.into(),snapshot.to_string().into()]).await?;
        Ok(())
    }
}

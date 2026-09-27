#![allow(elided_lifetimes_in_paths)]
#![allow(clippy::wildcard_imports)]
pub use sea_orm_migration::prelude::*;
mod m20260927_000001_conduit;
mod m20260927_000002_drafts;
mod m20260927_000003_tags_index;
mod m20260927_000004_exports;
mod m20260927_000005_article_shares;

pub struct Migrator;

#[async_trait::async_trait]
impl MigratorTrait for Migrator {
    fn migrations() -> Vec<Box<dyn MigrationTrait>> {
        vec![
            Box::new(m20260927_000001_conduit::Migration),
            Box::new(m20260927_000002_drafts::Migration),
            Box::new(m20260927_000003_tags_index::Migration),
            Box::new(m20260927_000004_exports::Migration),
            Box::new(m20260927_000005_article_shares::Migration),
        ]
    }
}

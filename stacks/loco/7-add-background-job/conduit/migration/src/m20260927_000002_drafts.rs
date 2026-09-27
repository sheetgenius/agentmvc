use sea_orm_migration::prelude::*;

#[derive(DeriveMigrationName)]
pub struct Migration;

#[async_trait::async_trait]
impl MigrationTrait for Migration {
    async fn up(&self, m: &SchemaManager) -> Result<(), DbErr> {
        m.alter_table(
            Table::alter()
                .table(Alias::new("articles"))
                .add_column(
                    ColumnDef::new(Alias::new("status"))
                        .string()
                        .not_null()
                        .default("published"),
                )
                .add_column(
                    ColumnDef::new(Alias::new("published_at"))
                        .timestamp_with_time_zone()
                        .default(Expr::current_timestamp()),
                )
                .add_column(
                    ColumnDef::new(Alias::new("revision"))
                        .integer()
                        .not_null()
                        .default(1),
                )
                .to_owned(),
        )
        .await
    }

    async fn down(&self, m: &SchemaManager) -> Result<(), DbErr> {
        m.alter_table(
            Table::alter()
                .table(Alias::new("articles"))
                .drop_column(Alias::new("revision"))
                .drop_column(Alias::new("published_at"))
                .drop_column(Alias::new("status"))
                .to_owned(),
        )
        .await
    }
}

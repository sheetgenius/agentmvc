use sea_orm_migration::prelude::*;

#[derive(DeriveMigrationName)]
pub struct Migration;

#[async_trait::async_trait]
impl MigrationTrait for Migration {
    async fn up(&self, m: &SchemaManager) -> Result<(), DbErr> {
        m.create_table(
            Table::create()
                .table(Alias::new("article_shares"))
                .if_not_exists()
                .col(
                    ColumnDef::new(Alias::new("id"))
                        .string()
                        .not_null()
                        .primary_key(),
                )
                .col(
                    ColumnDef::new(Alias::new("article_id"))
                        .big_integer()
                        .not_null()
                        .unique_key(),
                )
                .col(ColumnDef::new(Alias::new("key_hash")).string().not_null())
                .foreign_key(
                    ForeignKey::create()
                        .from(Alias::new("article_shares"), Alias::new("article_id"))
                        .to(Alias::new("articles"), Alias::new("id"))
                        .on_delete(ForeignKeyAction::Cascade),
                )
                .to_owned(),
        )
        .await
    }

    async fn down(&self, m: &SchemaManager) -> Result<(), DbErr> {
        m.drop_table(Table::drop().table(Alias::new("article_shares")).to_owned())
            .await
    }
}

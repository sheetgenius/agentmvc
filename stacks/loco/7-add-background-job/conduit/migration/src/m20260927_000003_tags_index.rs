use sea_orm_migration::prelude::*;

#[derive(DeriveMigrationName)]
pub struct Migration;

#[async_trait::async_trait]
impl MigrationTrait for Migration {
    async fn up(&self, m: &SchemaManager) -> Result<(), DbErr> {
        m.alter_table(
            Table::alter()
                .table(Alias::new("articles"))
                .modify_column(
                    ColumnDef::new(Alias::new("tag_list"))
                        .json_binary()
                        .not_null(),
                )
                .to_owned(),
        )
        .await?;
        m.create_index(
            Index::create()
                .name("articles_tag_list_gin")
                .table(Alias::new("articles"))
                .col(Alias::new("tag_list"))
                .index_type(IndexType::Custom(Alias::new("gin").into_iden()))
                .to_owned(),
        )
        .await
    }

    async fn down(&self, m: &SchemaManager) -> Result<(), DbErr> {
        m.drop_index(
            Index::drop()
                .name("articles_tag_list_gin")
                .table(Alias::new("articles"))
                .to_owned(),
        )
        .await?;
        m.alter_table(
            Table::alter()
                .table(Alias::new("articles"))
                .modify_column(ColumnDef::new(Alias::new("tag_list")).json().not_null())
                .to_owned(),
        )
        .await
    }
}

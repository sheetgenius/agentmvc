defmodule Conduit.Repo.Migrations.AddArticleExports do
  use Ecto.Migration

  def up do
    Oban.Migration.up()

    create table(:article_exports) do
      add :user_id, references(:users, on_delete: :delete_all), null: false
      add :status, :string, null: false, default: "pending"
      add :articles, {:array, :map}
      add :completed_at, :utc_datetime_usec
      timestamps(type: :utc_datetime_usec)
    end

    create index(:article_exports, [:user_id])
  end

  def down do
    drop table(:article_exports)
    Oban.Migration.down(version: 1)
  end
end

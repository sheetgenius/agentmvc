defmodule Conduit.Repo.Migrations.AddArticleDrafts do
  use Ecto.Migration
  import Ecto.Query

  def change do
    alter table(:articles) do
      add :status, :string, null: false, default: "published"
      add :published_at, :utc_datetime_usec
      add :revision, :integer, null: false, default: 1
    end

    flush()
    repo().update_all(from(a in "articles", update: [set: [published_at: a.inserted_at]]), [])

    create index(:articles, [:status])
  end
end

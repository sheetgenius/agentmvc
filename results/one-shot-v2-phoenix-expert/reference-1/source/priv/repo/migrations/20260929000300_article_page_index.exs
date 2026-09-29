defmodule Conduit.Repo.Migrations.ArticlePageIndex do
  use Ecto.Migration

  def up do
    drop index(:articles, [:status, :inserted_at])
    create index(:articles, [:status, :inserted_at, :id])
  end

  def down do
    drop index(:articles, [:status, :inserted_at, :id])
    create index(:articles, [:status, :inserted_at])
  end
end

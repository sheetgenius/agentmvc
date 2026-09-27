defmodule Conduit.Repo.Migrations.IndexFavoritesByArticle do
  use Ecto.Migration

  def change do
    create index(:favorites, [:article_id])
  end
end

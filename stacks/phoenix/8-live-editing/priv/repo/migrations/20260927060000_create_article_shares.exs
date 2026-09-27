defmodule Conduit.Repo.Migrations.CreateArticleShares do
  use Ecto.Migration

  def change do
    create table(:article_shares, primary_key: false) do
      add :id, :string, primary_key: true
      add :key_hash, :binary, null: false
      add :article_id, references(:articles, on_delete: :delete_all), null: false
    end

    create unique_index(:article_shares, [:article_id])
  end
end

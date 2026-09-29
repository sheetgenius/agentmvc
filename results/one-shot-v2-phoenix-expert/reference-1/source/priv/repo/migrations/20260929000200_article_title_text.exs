defmodule Conduit.Repo.Migrations.ArticleTitleText do
  use Ecto.Migration

  def change do
    alter table(:articles) do
      modify :title, :text, from: :string, null: false
    end
  end
end

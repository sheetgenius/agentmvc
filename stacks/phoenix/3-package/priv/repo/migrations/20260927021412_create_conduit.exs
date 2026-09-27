defmodule Conduit.Repo.Migrations.CreateConduit do
  use Ecto.Migration

  def change do
    create table(:users) do
      add :username, :string, null: false
      add :email, :string, null: false
      add :password_hash, :string, null: false
      add :bio, :text
      add :image, :string
      timestamps(type: :utc_datetime_usec)
    end

    create unique_index(:users, [:username])
    create unique_index(:users, [:email])

    create table(:articles) do
      add :slug, :string, null: false
      add :title, :string, null: false
      add :description, :text, null: false
      add :body, :text, null: false
      add :tag_list, {:array, :string}, null: false, default: []
      add :author_id, references(:users, on_delete: :delete_all), null: false
      timestamps(type: :utc_datetime_usec)
    end

    create unique_index(:articles, [:slug])
    create index(:articles, [:author_id])

    create table(:comments) do
      add :body, :text, null: false
      add :author_id, references(:users, on_delete: :delete_all), null: false
      add :article_id, references(:articles, on_delete: :delete_all), null: false
      timestamps(type: :utc_datetime_usec)
    end

    create index(:comments, [:article_id])

    create table(:follows, primary_key: false) do
      add :follower_id, references(:users, on_delete: :delete_all), null: false
      add :followed_id, references(:users, on_delete: :delete_all), null: false
    end

    create unique_index(:follows, [:follower_id, :followed_id])

    create table(:favorites, primary_key: false) do
      add :user_id, references(:users, on_delete: :delete_all), null: false
      add :article_id, references(:articles, on_delete: :delete_all), null: false
    end

    create unique_index(:favorites, [:user_id, :article_id])
  end
end

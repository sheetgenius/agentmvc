defmodule Conduit.Repo.Migrations.CreateConduit do
  use Ecto.Migration

  def change do
    Oban.Migration.up(version: 12)

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

    create table(:follows, primary_key: false) do
      add :follower_id, references(:users, on_delete: :delete_all), primary_key: true
      add :followed_id, references(:users, on_delete: :delete_all), primary_key: true
    end

    create table(:articles) do
      add :author_id, references(:users, on_delete: :delete_all), null: false
      add :slug, :string, null: false
      add :title, :string, null: false
      add :description, :text, null: false
      add :body, :text, null: false
      add :tag_list, {:array, :string}, default: [], null: false
      add :status, :string, default: "published", null: false
      add :published_at, :utc_datetime_usec
      add :revision, :integer, default: 1, null: false
      timestamps(type: :utc_datetime_usec)
    end

    create unique_index(:articles, [:slug])
    create index(:articles, [:author_id])

    create table(:favorites, primary_key: false) do
      add :user_id, references(:users, on_delete: :delete_all), primary_key: true
      add :article_id, references(:articles, on_delete: :delete_all), primary_key: true
    end

    create table(:comments) do
      add :body, :text, null: false
      add :author_id, references(:users, on_delete: :delete_all), null: false
      add :article_id, references(:articles, on_delete: :delete_all), null: false
      timestamps(type: :utc_datetime_usec)
    end

    create index(:comments, [:article_id])

    create table(:shares) do
      add :public_id, :string, null: false
      add :key_hash, :binary, null: false
      add :article_id, references(:articles, on_delete: :delete_all), null: false
    end

    create unique_index(:shares, [:public_id])
    create unique_index(:shares, [:article_id])

    create table(:exports) do
      add :user_id, references(:users, on_delete: :delete_all), null: false
      add :status, :string, default: "pending", null: false
      add :articles, :map
      add :completed_at, :utc_datetime_usec
      timestamps(type: :utc_datetime_usec)
    end
  end
end

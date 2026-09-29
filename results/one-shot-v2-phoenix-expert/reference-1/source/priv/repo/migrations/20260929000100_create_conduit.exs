defmodule Conduit.Repo.Migrations.CreateConduit do
  use Ecto.Migration

  def change do
    create table(:users) do
      add :username, :string, null: false
      add :email, :string, null: false
      add :password_hash, :string, null: false
      add :bio, :text
      add :image, :text
      timestamps(type: :utc_datetime_usec)
    end

    create unique_index(:users, [:username])
    create unique_index(:users, [:email])

    create table(:follows, primary_key: false) do
      add :follower_id, references(:users, on_delete: :delete_all), null: false
      add :followed_id, references(:users, on_delete: :delete_all), null: false
    end

    create unique_index(:follows, [:follower_id, :followed_id])
    create constraint(:follows, :no_self_follow, check: "follower_id <> followed_id")

    create table(:articles) do
      add :author_id, references(:users, on_delete: :delete_all), null: false
      add :slug, :string, null: false
      add :title, :string, null: false
      add :description, :text, null: false
      add :body, :text, null: false
      add :tag_list, {:array, :string}, null: false, default: []
      add :status, :string, null: false, default: "published"
      add :published_at, :utc_datetime_usec
      add :revision, :integer, null: false, default: 1
      timestamps(type: :utc_datetime_usec)
    end

    create unique_index(:articles, [:slug])
    create index(:articles, [:author_id, :status, :inserted_at])
    create index(:articles, [:status, :inserted_at])
    create index(:articles, [:tag_list], using: :gin)
    create constraint(:articles, :valid_status, check: "status IN ('draft', 'published')")
    create constraint(:articles, :positive_revision, check: "revision >= 1")

    create constraint(:articles, :publication_state,
             check:
               "(status = 'draft' AND published_at IS NULL) OR (status = 'published' AND published_at IS NOT NULL)"
           )

    create table(:favorites, primary_key: false) do
      add :user_id, references(:users, on_delete: :delete_all), null: false
      add :article_id, references(:articles, on_delete: :delete_all), null: false
    end

    create unique_index(:favorites, [:user_id, :article_id])
    create index(:favorites, [:article_id])

    create table(:comments) do
      add :article_id, references(:articles, on_delete: :delete_all), null: false
      add :author_id, references(:users, on_delete: :delete_all), null: false
      add :body, :text, null: false
      timestamps(type: :utc_datetime_usec)
    end

    create index(:comments, [:article_id, :inserted_at])

    create table(:exports) do
      add :user_id, references(:users, on_delete: :delete_all), null: false
      add :status, :string, null: false, default: "pending"
      add :articles, {:array, :map}
      add :completed_at, :utc_datetime_usec
      timestamps(type: :utc_datetime_usec)
    end

    create constraint(:exports, :export_state,
             check:
               "(status = 'pending' AND completed_at IS NULL AND articles IS NULL) OR (status = 'done' AND completed_at IS NOT NULL AND articles IS NOT NULL)"
           )

    create table(:shares) do
      add :public_id, :string, null: false
      add :article_id, references(:articles, on_delete: :delete_all), null: false
      add :key_hash, :binary, null: false
      add :revoked_at, :utc_datetime_usec
      timestamps(type: :utc_datetime_usec)
    end

    create unique_index(:shares, [:public_id])
    create unique_index(:shares, [:article_id], where: "revoked_at IS NULL")
  end
end

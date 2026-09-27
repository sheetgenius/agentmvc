defmodule Conduit.Accounts.User do
  use Ecto.Schema
  import Ecto.Changeset

  schema "users" do
    field :username, :string
    field :email, :string
    field :password, :string, virtual: true, redact: true
    field :password_hash, :string, redact: true
    field :bio, :string
    field :image, :string
    field :followed_by_viewer, :boolean, virtual: true

    many_to_many :following, __MODULE__,
      join_through: "follows",
      join_keys: [follower_id: :id, followed_id: :id]

    many_to_many :favorites, Conduit.Content.Article, join_through: "favorites"
    timestamps(type: :utc_datetime_usec)
  end

  def registration_changeset(user, attrs) do
    user
    |> cast(attrs, [:username, :email, :password])
    |> validate_required([:username, :email, :password])
    |> validate_length(:password, min: 8)
    |> validate_format(:email, ~r/^[^\s@]+@[^\s@]+\.[^\s@]+$/)
    |> unique_constraint(:username)
    |> unique_constraint(:email)
    |> hash_password()
  end

  def update_changeset(user, attrs) do
    user
    |> cast(attrs, [:username, :email, :password, :bio, :image])
    |> validate_required([:username, :email])
    |> validate_format(:email, ~r/^[^\s@]+@[^\s@]+\.[^\s@]+$/)
    |> maybe_validate_password(attrs)
    |> unique_constraint(:username)
    |> unique_constraint(:email)
    |> hash_password()
  end

  defp maybe_validate_password(changeset, attrs) do
    if Map.has_key?(attrs, "password") do
      changeset
      |> validate_required([:password])
      |> validate_length(:password, min: 8)
    else
      changeset
    end
  end

  defp hash_password(changeset) do
    case {changeset.valid?, get_change(changeset, :password)} do
      {true, password} when is_binary(password) ->
        put_change(changeset, :password_hash, Bcrypt.hash_pwd_salt(password))

      _ ->
        changeset
    end
  end
end

defmodule Conduit.Accounts.User do
  use Ecto.Schema
  import Ecto.Changeset

  schema "users" do
    field :username, :string
    field :email, :string
    field :password_hash, :string
    field :password, :string, virtual: true
    field :bio, :string
    field :image, :string
    timestamps(type: :utc_datetime_usec)
  end

  def changeset(user, attrs, required \\ false) do
    user
    |> cast(attrs, [:username, :email, :bio, :image, :password])
    |> validate_required(if(required, do: [:username, :email, :password], else: []))
    |> validate_required(
      Enum.filter([:username, :email, :password], &Map.has_key?(attrs, Atom.to_string(&1)))
    )
    |> validate_format(:email, ~r/^[^\s@]+@[^\s@]+\.[^\s@]+$/)
    |> validate_length(:password, min: 8)
    |> maybe_hash_password()
    |> unique_constraint(:username)
    |> unique_constraint(:email)
  end

  defp maybe_hash_password(%Ecto.Changeset{valid?: true} = changeset) do
    case get_change(changeset, :password) do
      nil -> changeset
      password -> put_change(changeset, :password_hash, Bcrypt.hash_pwd_salt(password))
    end
  end

  defp maybe_hash_password(changeset), do: changeset
end

defmodule Conduit.User do
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
    |> cast(attrs, [:username, :email, :password, :bio, :image])
    |> validate_required([:username, :email])
    |> then(fn c ->
      if required or Map.has_key?(attrs, "password"),
        do: validate_required(c, [:password]),
        else: c
    end)
    |> validate_format(:email, ~r/^[^\s@]+@[^\s@]+\.[^\s@]+$/)
    |> validate_length(:password, min: 8)
    |> unique_constraint(:username)
    |> unique_constraint(:email)
    |> put_password()
  end

  defp put_password(c) do
    case get_change(c, :password) do
      password when is_binary(password) and byte_size(password) >= 8 ->
        salt = :crypto.strong_rand_bytes(16)
        digest = :crypto.pbkdf2_hmac(:sha256, password, salt, 100_000, 32)
        put_change(c, :password_hash, Base.encode64(salt <> digest))

      _ ->
        c
    end
  end

  def password_valid?(user, password) when is_binary(password) do
    with %__MODULE__{password_hash: encoded} when is_binary(encoded) <- user,
         {:ok, <<salt::binary-size(16), digest::binary-size(32)>>} <- Base.decode64(encoded) do
      Plug.Crypto.secure_compare(
        digest,
        :crypto.pbkdf2_hmac(:sha256, password, salt, 100_000, 32)
      )
    else
      _ -> false
    end
  end

  def password_valid?(_, _), do: false
end

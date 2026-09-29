defmodule Conduit.Shares.Share do
  use Ecto.Schema

  schema "shares" do
    field :public_id, :string
    belongs_to :article, Conduit.Articles.Article
    field :key_hash, :binary
    field :revoked_at, :utc_datetime_usec
    timestamps(type: :utc_datetime_usec)
  end
end

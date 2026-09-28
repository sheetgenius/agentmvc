defmodule Conduit.Share do
  use Ecto.Schema

  schema "shares" do
    field :public_id, :string
    field :key_hash, :binary
    belongs_to :article, Conduit.Article
  end
end

defmodule Conduit.Content.Share do
  use Ecto.Schema
  import Ecto.Changeset

  @primary_key {:id, :string, autogenerate: false}
  schema "article_shares" do
    field :key_hash, :binary
    belongs_to :article, Conduit.Content.Article
  end

  def changeset(share, attrs) do
    share
    |> cast(attrs, [:id, :key_hash, :article_id])
    |> validate_required([:id, :key_hash, :article_id])
    |> unique_constraint(:article_id)
  end
end

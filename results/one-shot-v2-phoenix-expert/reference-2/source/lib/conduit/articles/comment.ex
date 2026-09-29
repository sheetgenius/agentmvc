defmodule Conduit.Articles.Comment do
  use Ecto.Schema
  import Ecto.Changeset

  schema "comments" do
    belongs_to :article, Conduit.Articles.Article
    belongs_to :author, Conduit.Accounts.User
    field :body, :string
    timestamps(type: :utc_datetime_usec)
  end

  def changeset(comment, attrs) do
    comment |> cast(attrs, [:body]) |> validate_required([:body])
  end
end

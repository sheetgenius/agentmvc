defmodule Conduit.Content.Comment do
  use Ecto.Schema
  import Ecto.Changeset

  schema "comments" do
    field :body, :string
    belongs_to :author, Conduit.Accounts.User
    belongs_to :article, Conduit.Content.Article
    timestamps(type: :utc_datetime_usec)
  end

  def changeset(comment, attrs) do
    comment |> cast(attrs, [:body]) |> validate_required([:body])
  end
end

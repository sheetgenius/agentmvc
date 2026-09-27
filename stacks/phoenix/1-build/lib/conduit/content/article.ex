defmodule Conduit.Content.Article do
  use Ecto.Schema
  import Ecto.Changeset

  schema "articles" do
    field :slug, :string
    field :title, :string
    field :description, :string
    field :body, :string
    field :tag_list, {:array, :string}, default: []
    belongs_to :author, Conduit.Accounts.User
    has_many :comments, Conduit.Content.Comment

    many_to_many :fans, Conduit.Accounts.User,
      join_through: "favorites",
      join_keys: [article_id: :id, user_id: :id]

    timestamps(type: :utc_datetime_usec)
  end

  def changeset(article, attrs) do
    attrs =
      if Map.has_key?(attrs, "tagList"),
        do: Map.put(attrs, "tag_list", attrs["tagList"]),
        else: attrs

    article
    |> cast(attrs, [:title, :description, :body, :tag_list])
    |> validate_required([:title, :description, :body])
    |> reject_null_tags(attrs)
    |> slug_from_title()
    |> unique_constraint(:slug)
  end

  defp reject_null_tags(changeset, %{"tagList" => nil}),
    do: add_error(changeset, :tag_list, "can't be blank")

  defp reject_null_tags(changeset, _attrs), do: changeset

  defp slug_from_title(changeset) do
    case get_change(changeset, :title) do
      nil ->
        changeset

      title ->
        slug =
          title |> String.downcase() |> String.replace(~r/[^a-z0-9]+/, "-") |> String.trim("-")

        put_change(changeset, :slug, "#{slug}-#{String.slice(Ecto.UUID.generate(), 0, 8)}")
    end
  end
end

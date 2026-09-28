defmodule Conduit.Article do
  use Ecto.Schema
  import Ecto.Changeset

  schema "articles" do
    field :slug, :string
    field :title, :string
    field :description, :string
    field :body, :string
    field :tag_list, {:array, :string}, default: []
    field :status, :string, default: "published"
    field :published_at, :utc_datetime_usec
    field :revision, :integer, default: 1
    belongs_to :author, Conduit.User
    timestamps(type: :utc_datetime_usec)
  end

  def changeset(article, attrs, create? \\ false) do
    attrs =
      if Map.has_key?(attrs, "tagList"),
        do: Map.put(attrs, "tag_list", attrs["tagList"]),
        else: attrs

    article
    |> cast(attrs, [:title, :description, :body, :tag_list])
    |> then(fn c ->
      if create?, do: validate_required(c, [:title, :description, :body]), else: c
    end)
    |> validate_change(:tag_list, fn :tag_list, value ->
      if is_list(value) and Enum.all?(value, &is_binary/1), do: [], else: [tag_list: "is invalid"]
    end)
    |> then(fn c ->
      if Map.has_key?(attrs, "tag_list") and is_nil(attrs["tag_list"]),
        do: add_error(c, :tag_list, "is invalid"),
        else: c
    end)
  end
end

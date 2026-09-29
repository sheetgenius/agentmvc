defmodule Conduit.Articles.Article do
  use Ecto.Schema
  import Ecto.Changeset

  schema "articles" do
    belongs_to :author, Conduit.Accounts.User
    field :slug, :string
    field :title, :string
    field :description, :string
    field :body, :string
    field :tag_list, {:array, :string}, default: []
    field :status, :string, default: "published"
    field :published_at, :utc_datetime_usec
    field :revision, :integer, default: 1
    timestamps(type: :utc_datetime_usec)
  end

  def content_changeset(article, attrs, required \\ false) do
    article
    |> cast(attrs, [:title, :description, :body, :tag_list])
    |> reject_null_tags(attrs)
    |> validate_required(if(required, do: [:title, :description, :body], else: []))
    |> validate_required(
      Enum.filter([:title, :description, :body], &Map.has_key?(attrs, Atom.to_string(&1)))
    )
    |> validate_length(:title, max: 255)
    |> validate_change(:tag_list, fn :tag_list, tags ->
      if Enum.all?(tags, &(is_binary(&1) and byte_size(&1) <= 255)),
        do: [],
        else: [tag_list: "is invalid"]
    end)
    |> unique_constraint(:slug)
  end

  defp reject_null_tags(changeset, attrs) do
    if Map.has_key?(attrs, "tag_list") and is_nil(attrs["tag_list"]),
      do: add_error(changeset, :tag_list, "is invalid"),
      else: changeset
  end
end

defmodule Conduit.Content.Article do
  use Ecto.Schema
  import Ecto.Changeset

  schema "articles" do
    field :slug, :string
    field :title, :string
    field :description, :string
    field :body, :string
    field :tag_list, {:array, :string}, default: []
    field :status, Ecto.Enum, values: [:draft, :published], default: :published
    field :published_at, :utc_datetime_usec
    field :revision, :integer, default: 1
    field :favorited_by_viewer, :boolean, virtual: true
    field :favorites_count, :integer, virtual: true
    belongs_to :author, Conduit.Accounts.User
    has_many :comments, Conduit.Content.Comment

    many_to_many :fans, Conduit.Accounts.User,
      join_through: "favorites",
      join_keys: [article_id: :id, user_id: :id]

    timestamps(type: :utc_datetime_usec)
  end

  def create_changeset(article, attrs) do
    article
    |> changeset(attrs)
    |> cast(attrs, [:status])
    |> published_at_creation()
  end

  def update_changeset(article, attrs) do
    article
    |> changeset(attrs)
    |> optimistic_lock(:revision)
  end

  def publish_changeset(article) do
    article
    |> change(status: :published, published_at: DateTime.utc_now())
    |> optimistic_lock(:revision)
  end

  def check_revision(article, %{"revision" => revision}) when not is_integer(revision),
    do: {:error, article |> change() |> add_error(:revision, "is invalid")}

  def check_revision(%{revision: revision}, %{"revision" => revision}), do: :ok
  def check_revision(article, %{"revision" => _}), do: {:stale, article}
  def check_revision(_, _), do: :ok

  defp changeset(article, attrs) do
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

  defp published_at_creation(changeset) do
    if get_field(changeset, :status) == :published,
      do: put_change(changeset, :published_at, DateTime.utc_now()),
      else: changeset
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

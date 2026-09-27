defmodule Conduit.Content do
  import Ecto.Query
  alias Conduit.Content.{Article, Comment}
  alias Conduit.Accounts.User
  alias Conduit.Repo

  def fetch_article(slug, viewer) do
    viewer_id = viewer && viewer.id

    case Repo.get_by(Article, slug: slug) do
      nil ->
        {:error, :article}

      %Article{status: :draft, author_id: author_id} when author_id != viewer_id ->
        {:error, :article}

      article ->
        {:ok, Repo.preload(article, :author)}
    end
  end

  def create_article(author, attrs) do
    %Article{author_id: author.id}
    |> Article.create_changeset(attrs)
    |> Repo.insert()
    |> preload_author()
  end

  def update_article(article, attrs) do
    with :ok <- Article.check_revision(article, attrs) do
      article |> Article.update_changeset(attrs) |> Repo.update() |> preload_author()
    end
  rescue
    Ecto.StaleEntryError -> {:stale, Repo.get!(Article, article.id) |> Repo.preload(:author)}
  end

  def publish_article(%Article{status: :published} = article), do: {:ok, article}

  def publish_article(article) do
    article |> Article.publish_changeset() |> Repo.update() |> preload_author()
  rescue
    Ecto.StaleEntryError ->
      Article |> Repo.get!(article.id) |> Repo.preload(:author) |> publish_article()
  end

  def delete_article(article), do: Repo.delete(article)

  def list_articles(params) do
    query =
      published_articles()
      |> filter(:author, params["author"])
      |> filter(:favorited, params["favorited"])
      |> filter(:tag, params["tag"])

    page(query, params)
  end

  def feed(viewer, params) do
    published_articles()
    |> join(:inner, [a], f in "follows", on: f.followed_id == a.author_id)
    |> where([a, f], f.follower_id == ^viewer.id)
    |> page(params)
  end

  def tags do
    published_articles()
    |> select([a], a.tag_list)
    |> Repo.all()
    |> List.flatten()
    |> Enum.uniq()
    |> Enum.sort()
  end

  def drafts(viewer, params) do
    Article
    |> where([a], a.status == :draft and a.author_id == ^viewer.id)
    |> page(params)
  end

  def favorite(viewer, article) do
    with :ok <- ensure_published(article) do
      Repo.insert_all("favorites", [%{user_id: viewer.id, article_id: article.id}],
        on_conflict: :nothing
      )

      :ok
    end
  end

  def unfavorite(viewer, article) do
    with :ok <- ensure_published(article) do
      Repo.delete_all(
        from f in "favorites", where: f.user_id == ^viewer.id and f.article_id == ^article.id
      )

      :ok
    end
  end

  def favorited?(nil, _article), do: false

  def favorited?(viewer, article) do
    Repo.exists?(from a in Ecto.assoc(viewer, :favorites), where: a.id == ^article.id)
  end

  def favorites_count(article), do: Repo.aggregate(Ecto.assoc(article, :fans), :count, :id)

  def list_comments(article),
    do:
      article
      |> Ecto.assoc(:comments)
      |> order_by(asc: :id)
      |> Repo.all()
      |> Repo.preload(:author)

  def get_comment(article, id), do: Repo.get_by(Comment, article_id: article.id, id: id)

  def create_comment(article, author, attrs) do
    with :ok <- ensure_published(article) do
      %Comment{article_id: article.id, author_id: author.id}
      |> Comment.changeset(attrs)
      |> Repo.insert()
      |> preload_author()
    end
  end

  def delete_comment(comment), do: Repo.delete(comment)

  defp published_articles, do: where(Article, status: :published)
  defp ensure_published(%Article{status: :draft}), do: {:draft, :article}
  defp ensure_published(_), do: :ok

  defp filter(query, _, nil), do: query

  defp filter(query, :author, username),
    do: join(query, :inner, [a], u in assoc(a, :author), on: u.username == ^username)

  defp filter(query, :favorited, username) do
    query
    |> join(:inner, [a], f in "favorites", on: f.article_id == a.id)
    |> join(:inner, [a, f], u in User, on: u.id == f.user_id and u.username == ^username)
  end

  defp filter(query, :tag, tag), do: where(query, [a], ^tag in a.tag_list)

  defp page(query, params) do
    count = Repo.aggregate(query, :count, :id)
    limit = positive_integer(params["limit"], 20)
    offset = positive_integer(params["offset"], 0)

    articles =
      query
      |> order_by([a], desc: a.inserted_at, desc: a.id)
      |> limit(^limit)
      |> offset(^offset)
      |> Repo.all()
      |> Repo.preload(:author)

    {articles, count}
  end

  defp positive_integer(nil, default), do: default

  defp positive_integer(value, default) do
    case Integer.parse(value) do
      {n, ""} when n >= 0 -> n
      _ -> default
    end
  end

  defp preload_author({:ok, record}), do: {:ok, Repo.preload(record, :author)}
  defp preload_author(error), do: error
end

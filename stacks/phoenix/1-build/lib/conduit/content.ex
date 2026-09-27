defmodule Conduit.Content do
  import Ecto.Query
  alias Conduit.Content.{Article, Comment}
  alias Conduit.Accounts.User
  alias Conduit.Repo

  def fetch_article(slug) do
    case Repo.get_by(Article, slug: slug) do
      nil -> {:error, :article}
      article -> {:ok, Repo.preload(article, :author)}
    end
  end

  def create_article(author, attrs) do
    %Article{author_id: author.id}
    |> Article.changeset(attrs)
    |> Repo.insert()
    |> preload_author()
  end

  def update_article(article, attrs) do
    article |> Article.changeset(attrs) |> Repo.update() |> preload_author()
  end

  def delete_article(article), do: Repo.delete(article)

  def list_articles(params) do
    query =
      Article
      |> filter(:author, params["author"])
      |> filter(:favorited, params["favorited"])
      |> filter(:tag, params["tag"])

    page(query, params)
  end

  def feed(viewer, params) do
    Article
    |> join(:inner, [a], f in "follows", on: f.followed_id == a.author_id)
    |> where([a, f], f.follower_id == ^viewer.id)
    |> page(params)
  end

  def tags do
    Repo.all(from a in Article, select: a.tag_list)
    |> List.flatten()
    |> Enum.uniq()
    |> Enum.sort()
  end

  def favorite(viewer, article) do
    Repo.insert_all("favorites", [%{user_id: viewer.id, article_id: article.id}],
      on_conflict: :nothing
    )

    :ok
  end

  def unfavorite(viewer, article) do
    Repo.delete_all(
      from f in "favorites", where: f.user_id == ^viewer.id and f.article_id == ^article.id
    )

    :ok
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
    %Comment{article_id: article.id, author_id: author.id}
    |> Comment.changeset(attrs)
    |> Repo.insert()
    |> preload_author()
  end

  def delete_comment(comment), do: Repo.delete(comment)

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

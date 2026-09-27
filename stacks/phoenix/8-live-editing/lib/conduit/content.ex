defmodule Conduit.Content do
  import Ecto.Query
  alias Conduit.Content.{Article, Comment, Share}
  alias Conduit.Accounts.User
  alias Conduit.Repo

  def fetch_article(slug, viewer) do
    viewer_id = viewer && viewer.id

    query =
      from a in Article,
        where: a.slug == ^slug,
        join: author in assoc(a, :author),
        preload: [author: author]

    case Repo.one(query) do
      nil ->
        {:error, :article}

      %Article{status: :draft, author_id: author_id} when author_id != viewer_id ->
        {:error, :article}

      article ->
        {:ok, article}
    end
  end

  def create_article(author, attrs) do
    with {:ok, article} <-
           %Article{author_id: author.id} |> Article.create_changeset(attrs) |> Repo.insert() do
      {:ok, %{article | author: author}}
    end
  end

  def update_article(article, author, attrs) do
    with :ok <- ensure_author(article, author),
         :ok <- Article.check_revision(article, attrs) do
      article |> Article.update_changeset(attrs) |> Repo.update() |> preload_author()
    end
  rescue
    Ecto.StaleEntryError -> {:stale, Repo.get!(Article, article.id) |> Repo.preload(:author)}
  end

  def update_article_and_notify(article, author, attrs) do
    article |> update_article(author, attrs) |> notify_updated()
  end

  def publish_article(article, author) do
    with :ok <- ensure_author(article, author), do: do_publish_article(article)
  end

  defp do_publish_article(%Article{status: :published} = article), do: {:ok, article}

  defp do_publish_article(article) do
    article
    |> Article.publish_changeset()
    |> Repo.update()
    |> preload_author()
    |> notify_updated()
  rescue
    Ecto.StaleEntryError ->
      Article |> Repo.get!(article.id) |> Repo.preload(:author) |> do_publish_article()
  end

  def delete_article(article, author) do
    with :ok <- ensure_author(article, author) do
      share_id = Repo.one(from s in Share, where: s.article_id == ^article.id, select: s.id)

      case Repo.delete(article) do
        {:ok, _} = result ->
          if share_id, do: Conduit.LiveRooms.revoke(share_id)
          result

        error ->
          error
      end
    end
  end

  def list_articles(params, viewer) do
    query =
      published_articles()
      |> filter(:author, params["author"])
      |> filter(:favorited, params["favorited"])
      |> filter(:tag, params["tag"])

    page(query, params, viewer)
  end

  def feed(viewer, params) do
    published_articles()
    |> join(:inner, [a], f in "follows", on: f.followed_id == a.author_id)
    |> where([a, f], f.follower_id == ^viewer.id)
    |> page(params, viewer)
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
    |> page(params, viewer)
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

  def favorite_stats(%Article{favorites_count: count, favorited_by_viewer: favorited}, _viewer)
      when is_integer(count) and is_boolean(favorited),
      do: {favorited, count}

  def favorite_stats(article, nil),
    do: {false, Repo.aggregate(Ecto.assoc(article, :fans), :count, :id)}

  def favorite_stats(article, viewer) do
    {count, viewer_count} =
      from(f in "favorites",
        where: f.article_id == ^article.id,
        select: {count(f.article_id), filter(count(f.user_id), f.user_id == ^viewer.id)}
      )
      |> Repo.one()

    {viewer_count > 0, count}
  end

  def list_comments(article) do
    article
    |> Ecto.assoc(:comments)
    |> order_by(asc: :id)
    |> Repo.all()
    |> Repo.preload(:author)
  end

  def get_comment(article, id), do: Repo.get_by(Comment, article_id: article.id, id: id)

  def create_comment(article, author, attrs) do
    with :ok <- ensure_published(article),
         {:ok, comment} <-
           %Comment{article_id: article.id, author_id: author.id}
           |> Comment.changeset(attrs)
           |> Repo.insert() do
      {:ok, %{comment | author: author}}
    end
  end

  def delete_comment(comment, author) do
    with :ok <- ensure_author(comment, author), do: Repo.delete(comment)
  end

  defp published_articles, do: where(Article, status: :published)
  defp ensure_published(%Article{status: :draft}), do: {:draft, :article}
  defp ensure_published(_), do: :ok
  defp ensure_author(record, author) when record.author_id == author.id, do: :ok
  defp ensure_author(%Article{}, _), do: {:forbidden, :article}
  defp ensure_author(%Comment{}, _), do: {:forbidden, :comment}

  defp filter(query, _, nil), do: query

  defp filter(query, :author, username),
    do: join(query, :inner, [a], u in assoc(a, :author), on: u.username == ^username)

  defp filter(query, :favorited, username) do
    query
    |> join(:inner, [a], f in "favorites", on: f.article_id == a.id)
    |> join(:inner, [a, f], u in User, on: u.id == f.user_id and u.username == ^username)
  end

  defp filter(query, :tag, tag), do: where(query, [a], ^tag in a.tag_list)

  defp page(query, params, viewer) do
    count = Repo.aggregate(query, :count, :id)
    limit = nonnegative_integer(params["limit"], 20, 100)
    offset = nonnegative_integer(params["offset"], 0, 9_223_372_036_854_775_807)

    articles =
      query
      |> order_by([a], desc: a.inserted_at, desc: a.id)
      |> limit(^limit)
      |> offset(^offset)
      |> Repo.all()
      |> Repo.preload(:author)
      |> listing_data(viewer)

    {articles, count}
  end

  defp listing_data([], _viewer), do: []

  defp listing_data(articles, viewer) do
    article_ids = Enum.map(articles, & &1.id)

    counts =
      from(f in "favorites",
        where: f.article_id in ^article_ids,
        group_by: f.article_id,
        select: {f.article_id, count()}
      )
      |> Repo.all()
      |> Map.new()

    {favorites, following} = viewer_relationships(articles, viewer)

    Enum.map(articles, fn article ->
      author = %{
        article.author
        | followed_by_viewer: MapSet.member?(following, article.author_id)
      }

      %{
        article
        | author: author,
          favorites_count: Map.get(counts, article.id, 0),
          favorited_by_viewer: MapSet.member?(favorites, article.id)
      }
    end)
  end

  defp viewer_relationships(_articles, nil), do: {MapSet.new(), MapSet.new()}

  defp viewer_relationships(articles, viewer) do
    article_ids = Enum.map(articles, & &1.id)
    author_ids = Enum.map(articles, & &1.author_id)

    favorites =
      from(f in "favorites",
        where: f.user_id == ^viewer.id and f.article_id in ^article_ids,
        select: f.article_id
      )
      |> Repo.all()
      |> MapSet.new()

    following =
      from(f in "follows",
        where: f.follower_id == ^viewer.id and f.followed_id in ^author_ids,
        select: f.followed_id
      )
      |> Repo.all()
      |> MapSet.new()

    {favorites, following}
  end

  defp nonnegative_integer(value, default, max) when is_binary(value) do
    case Integer.parse(value) do
      {n, ""} when n >= 0 and n <= max -> n
      _ -> default
    end
  end

  defp nonnegative_integer(_, default, _max), do: default

  defp preload_author({:ok, record}), do: {:ok, Repo.preload(record, :author)}
  defp preload_author(error), do: error

  defp notify_updated({:ok, article} = result) do
    Conduit.LiveRooms.updated(article)
    result
  end

  defp notify_updated(other), do: other
end

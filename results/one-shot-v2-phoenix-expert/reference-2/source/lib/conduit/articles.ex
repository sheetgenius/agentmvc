defmodule Conduit.Articles do
  import Ecto.Query
  alias Conduit.Repo
  alias Conduit.Accounts
  alias Conduit.Articles.{Article, Comment}

  @type caller :: :anonymous | {:user, Accounts.User.t()}

  def slug_for(title) do
    stem =
      title
      |> String.downcase()
      |> String.replace(~r/[^a-z0-9]+/u, "-")
      |> String.trim("-")
      |> String.slice(0, 244)
      |> String.trim_trailing("-")

    if(stem == "", do: "article", else: stem) <>
      "-" <> Base.encode16(:crypto.strong_rand_bytes(5), case: :lower)
  end

  def visible?(%Article{status: "published"}, _caller), do: true
  def visible?(%Article{author_id: id}, {:user, %{id: id}}), do: true
  def visible?(_article, _caller), do: false

  def get_visible(slug, caller) do
    case Repo.get_by(Article, slug: slug) do
      %Article{} = article -> if visible?(article, caller), do: {:ok, article}, else: missing()
      _ -> missing()
    end
  end

  def get_published(slug, caller) do
    with {:ok, article} <- get_visible(slug, caller),
         :ok <- ensure_published(article) do
      {:ok, article}
    end
  end

  def ensure_published(%Article{status: "draft"}), do: {:error, {:article, "is a draft"}}
  def ensure_published(_), do: :ok
  def owner(%Article{author_id: id}, %{id: id}), do: :ok
  def owner(_, _), do: {:error, {:article, "forbidden"}}

  def create(user, attrs) when is_map(attrs) do
    status = Map.get(attrs, "status", "published")

    if status in ["draft", "published"] do
      now = DateTime.utc_now()

      %Article{
        author_id: user.id,
        status: status,
        published_at: if(status == "published", do: now)
      }
      |> Article.content_changeset(normalize_tags(attrs), true)
      |> Ecto.Changeset.put_change(
        :slug,
        slug_for(if(is_binary(attrs["title"]), do: attrs["title"], else: ""))
      )
      |> Repo.insert()
      |> preload_result()
    else
      {:error, {:validation, %{"status" => ["is invalid"]}}}
    end
  end

  def create(_, _), do: {:error, {:validation, %{"article" => ["is invalid"]}}}

  # Both entrances use one locked content commit. A share is checked again under the lock.
  def author_edit(user, slug) do
    with {:ok, article} <- get_visible(slug, {:user, user}),
         :ok <- owner(article, user) do
      {:ok, article}
    end
  end

  def commit({:author, user, %Article{} = article}, attrs) do
    locked_commit(article.id, {:author, user}, attrs)
  end

  def commit({:share, share_id, key}, attrs) do
    with {:ok, share} <- Conduit.Shares.authorize(share_id, key),
         :ok <- shared_shape(attrs) do
      locked_commit(share.article_id, {:share, share_id, key}, attrs)
    end
  end

  defp shared_shape(%{"title" => title, "body" => body, "revision" => revision} = attrs)
       when map_size(attrs) == 3 and is_binary(title) and is_binary(body) and is_integer(revision),
       do: :ok

  defp shared_shape(_), do: {:error, {:validation, %{"article" => ["is invalid"]}}}

  defp locked_commit(id, entrance, attrs) do
    result =
      Repo.transaction(fn ->
        article = Repo.one(from a in Article, where: a.id == ^id, lock: "FOR UPDATE")

        with %Article{} <- article,
             :ok <- recheck_entrance(entrance, article),
             :ok <- check_revision(attrs, article),
             {:ok, edited} <- update_content(article, attrs) do
          edited
        else
          nil -> Repo.rollback({:article, "not found"})
          {:error, reason} -> Repo.rollback(reason)
        end
      end)

    case result do
      {:ok, article} ->
        broadcast_update(article)
        {:ok, Repo.preload(article, :author)}

      {:error, reason} ->
        {:error, reason}
    end
  end

  defp recheck_entrance({:author, user}, article) do
    if visible?(article, {:user, user}), do: owner(article, user), else: missing()
  end

  defp recheck_entrance({:share, id, key}, article) do
    case Conduit.Shares.authorize(id, key) do
      {:ok, %{article_id: article_id}} when article_id == article.id -> :ok
      _ -> {:error, {:share, "not found"}}
    end
  end

  defp check_revision(attrs, article) do
    case Map.fetch(attrs, "revision") do
      :error -> :ok
      {:ok, revision} when is_integer(revision) and revision == article.revision -> :ok
      {:ok, revision} when is_integer(revision) -> {:error, {:stale, article}}
      _ -> {:error, {:validation, %{"revision" => ["is invalid"]}}}
    end
  end

  defp update_content(article, attrs) when is_map(attrs) do
    attrs = normalize_tags(attrs)
    changeset = Article.content_changeset(article, attrs)

    changeset =
      if Ecto.Changeset.get_change(changeset, :title) do
        Ecto.Changeset.put_change(changeset, :slug, slug_for(attrs["title"]))
      else
        changeset
      end

    changeset
    |> Ecto.Changeset.put_change(:revision, article.revision + 1)
    |> Repo.update()
  end

  defp update_content(_, _), do: {:error, {:validation, %{"article" => ["is invalid"]}}}

  def publish(user, slug) do
    with {:ok, article} <- get_visible(slug, {:user, user}), :ok <- owner(article, user) do
      result =
        Repo.transaction(fn ->
          locked = Repo.one!(from a in Article, where: a.id == ^article.id, lock: "FOR UPDATE")

          if locked.status == "published" do
            locked
          else
            {:ok, saved} =
              locked
              |> Ecto.Changeset.change(
                status: "published",
                published_at: DateTime.utc_now(),
                revision: locked.revision + 1
              )
              |> Repo.update()

            saved
          end
        end)

      case result do
        {:ok, saved} ->
          if saved.revision != article.revision, do: broadcast_update(saved)
          {:ok, Repo.preload(saved, :author)}

        error ->
          error
      end
    end
  end

  def delete(user, slug) do
    with {:ok, article} <- get_visible(slug, {:user, user}), :ok <- owner(article, user) do
      Repo.delete(article)
    end
  end

  def list(kind, caller, params) do
    query = discovery_query(kind, caller, params)
    count = Repo.aggregate(query, :count, :id)
    {limit, offset} = page(params)

    articles =
      query
      |> order_by([a], desc: a.inserted_at, desc: a.id)
      |> limit(^limit)
      |> offset(^offset)
      |> Repo.all()

    {present(articles, caller, false), count}
  end

  defp discovery_query(:drafts, {:user, user}, _params) do
    from a in Article, where: a.status == "draft" and a.author_id == ^user.id
  end

  defp discovery_query(:feed, {:user, user}, _params) do
    from a in Article,
      where: a.status == "published",
      where:
        a.author_id in subquery(
          from f in "follows", where: f.follower_id == ^user.id, select: f.followed_id
        )
  end

  defp discovery_query(:global, _caller, params) do
    query = from a in Article, where: a.status == "published"

    query =
      case params["tag"] do
        tag when is_binary(tag) ->
          where(query, [a], fragment("? @> ?", a.tag_list, type(^[tag], {:array, :string})))

        _ ->
          query
      end

    query =
      case params["author"] do
        name when is_binary(name) ->
          where(
            query,
            [a],
            a.author_id in subquery(
              from u in Conduit.Accounts.User, where: u.username == ^name, select: u.id
            )
          )

        _ ->
          query
      end

    case params["favorited"] do
      name when is_binary(name) ->
        where(
          query,
          [a],
          a.id in subquery(
            from f in "favorites",
              join: u in Conduit.Accounts.User,
              on: u.id == f.user_id,
              where: u.username == ^name,
              select: f.article_id
          )
        )

      _ ->
        query
    end
  end

  defp page(params) do
    {number(params["limit"], 20, 100), number(params["offset"], 0, 1_000_000)}
  end

  defp number(value, default, max) when is_binary(value) do
    case Integer.parse(value) do
      {n, ""} when n >= 0 -> min(n, max)
      _ -> default
    end
  end

  defp number(_, default, _), do: default

  def tags do
    Repo.all(
      from a in Article,
        where: a.status == "published",
        select: fragment("DISTINCT unnest(?)", a.tag_list)
    )
    |> Enum.sort()
  end

  def favorite(user, article, active?) do
    with :ok <- ensure_published(article) do
      if active? do
        Repo.insert_all("favorites", [%{user_id: user.id, article_id: article.id}],
          on_conflict: :nothing
        )
      else
        Repo.delete_all(
          from f in "favorites", where: f.user_id == ^user.id and f.article_id == ^article.id
        )
      end

      {:ok, article}
    end
  end

  def create_comment(user, article, attrs) do
    with :ok <- ensure_published(article) do
      %Comment{article_id: article.id, author_id: user.id}
      |> Comment.changeset(attrs)
      |> Repo.insert()
      |> preload_result()
    end
  end

  def comments(article, caller) do
    article.id
    |> then(fn id ->
      Repo.all(
        from c in Comment,
          where: c.article_id == ^id,
          order_by: [asc: c.inserted_at, asc: c.id],
          preload: [:author]
      )
    end)
    |> present_comments(caller)
  end

  def delete_comment(user, article, id) do
    with {:ok, id} <- Conduit.Id.parse(id),
         %Comment{} = comment <- Repo.get_by(Comment, id: id, article_id: article.id),
         true <- comment.author_id == user.id do
      Repo.delete(comment)
    else
      false -> {:error, {:comment, "forbidden"}}
      _ -> {:error, {:comment, "not found"}}
    end
  end

  def present([_ | _] = articles, caller, include_body) do
    ids = Enum.map(articles, & &1.id)
    author_ids = Enum.map(articles, & &1.author_id) |> Enum.uniq()

    authors =
      Repo.all(from u in Conduit.Accounts.User, where: u.id in ^author_ids)
      |> Map.new(&{&1.id, &1})

    counts =
      Repo.all(
        from f in "favorites",
          where: f.article_id in ^ids,
          group_by: f.article_id,
          select: {f.article_id, count(f.user_id)}
      )
      |> Map.new()

    {favorited, following} =
      case caller do
        {:user, viewer} ->
          fav =
            Repo.all(
              from f in "favorites",
                where: f.user_id == ^viewer.id and f.article_id in ^ids,
                select: f.article_id
            )
            |> MapSet.new()

          fol =
            Repo.all(
              from f in "follows",
                where: f.follower_id == ^viewer.id and f.followed_id in ^author_ids,
                select: f.followed_id
            )
            |> MapSet.new()

          {fav, fol}

        _ ->
          {MapSet.new(), MapSet.new()}
      end

    Enum.map(articles, fn article ->
      author = Map.fetch!(authors, article.author_id)

      base = %{
        slug: article.slug,
        title: article.title,
        description: article.description,
        tagList: article.tag_list,
        createdAt: iso(article.inserted_at),
        updatedAt: iso(article.updated_at),
        favorited: MapSet.member?(favorited, article.id),
        favoritesCount: Map.get(counts, article.id, 0),
        status: article.status,
        publishedAt: iso(article.published_at),
        revision: article.revision,
        author: %{
          username: author.username,
          bio: author.bio,
          image: author.image,
          following: MapSet.member?(following, author.id)
        }
      }

      if include_body, do: Map.put(base, :body, article.body), else: base
    end)
  end

  def present([], _caller, _include_body), do: []
  def present_one(article, caller), do: hd(present([article], caller, true))

  def shared(article),
    do: %{
      slug: article.slug,
      title: article.title,
      body: article.body,
      revision: article.revision
    }

  def present_comments(comments, caller) do
    author_ids = Enum.map(comments, & &1.author_id) |> Enum.uniq()

    following =
      case caller do
        {:user, viewer} ->
          Repo.all(
            from f in "follows",
              where: f.follower_id == ^viewer.id and f.followed_id in ^author_ids,
              select: f.followed_id
          )
          |> MapSet.new()

        _ ->
          MapSet.new()
      end

    Enum.map(comments, fn comment ->
      author = comment.author

      %{
        id: comment.id,
        body: comment.body,
        createdAt: iso(comment.inserted_at),
        updatedAt: iso(comment.updated_at),
        author: %{
          username: author.username,
          bio: author.bio,
          image: author.image,
          following: MapSet.member?(following, author.id)
        }
      }
    end)
  end

  defp iso(nil), do: nil
  defp iso(value), do: DateTime.to_iso8601(value)
  defp missing, do: {:error, {:article, "not found"}}
  defp preload_result({:ok, record}), do: {:ok, Repo.preload(record, :author)}
  defp preload_result(other), do: other

  defp normalize_tags(attrs),
    do:
      if(Map.has_key?(attrs, "tagList"),
        do: attrs |> Map.put("tag_list", attrs["tagList"]) |> Map.delete("tagList"),
        else: attrs
      )

  defp broadcast_update(article) do
    Phoenix.PubSub.broadcast(
      Conduit.PubSub,
      "article:#{article.id}",
      {:article_updated, article.id, shared(article)}
    )
  end
end

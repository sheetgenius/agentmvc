defmodule Conduit.Content do
  import Ecto.Query
  alias Conduit.{Repo, Article, Comment, User, Share}

  def article(slug, viewer) do
    case Repo.get_by(Article, slug: slug) do
      nil ->
        {:not_found, :article}

      %Article{status: "draft", author_id: id} = article ->
        if viewer && viewer.id == id, do: {:ok, article}, else: {:not_found, :article}

      article ->
        {:ok, article}
    end
  end

  def owned(slug, viewer) do
    with {:ok, article} <- article(slug, viewer) do
      if article.author_id == viewer.id, do: {:ok, article}, else: {:forbidden, :article}
    end
  end

  def create(viewer, attrs) when is_map(attrs) do
    status = Map.get(attrs, "status", "published")

    if status in ["draft", "published"] do
      title = attrs["title"]
      initial_slug = if is_binary(title), do: slug(title, random(6)), else: random(12)

      case %Article{
             author_id: viewer.id,
             status: status,
             published_at: published_at(status),
             slug: initial_slug
           }
           |> Article.changeset(attrs, true)
           |> Repo.insert() do
        {:ok, article} ->
          slug = slug(article.title, article.id)
          Repo.update(Ecto.Changeset.change(article, slug: slug))

        error ->
          error
      end
    else
      {:error, %{status: ["is invalid"]}}
    end
  end

  def create(_, _), do: {:error, %{article: ["is invalid"]}}

  def update(article, attrs, viewer, shared? \\ false)

  def update(article, attrs, viewer, shared?) when is_map(attrs) do
    result =
      Repo.transaction(fn ->
        current = Repo.one!(from a in Article, where: a.id == ^article.id, lock: "FOR UPDATE")

        case update_locked(current, attrs, viewer, shared?) do
          {:ok, updated} -> updated
          error -> Repo.rollback(error)
        end
      end)

    case result do
      {:ok, updated} ->
        Conduit.Rooms.updated(updated)
        {:ok, updated}

      {:error, error} ->
        error
    end
  end

  def update(_, _, _, _), do: {:error, %{article: ["is invalid"]}}

  defp update_locked(article, attrs, viewer, shared?) do
    cond do
      not shared? and article.author_id != viewer.id ->
        {:forbidden, :article}

      shared? and Enum.any?(Map.keys(attrs), &(&1 not in ~w(title body revision))) ->
        {:error, %{article: ["is invalid"]}}

      shared? and not Enum.all?(~w(title body revision), &Map.has_key?(attrs, &1)) ->
        {:error, %{article: ["is invalid"]}}

      Map.has_key?(attrs, "revision") and not is_integer(attrs["revision"]) ->
        {:error, %{revision: ["is invalid"]}}

      shared? and attrs["revision"] != article.revision ->
        {:stale, article}

      Map.has_key?(attrs, "revision") and attrs["revision"] != article.revision ->
        {:stale, article}

      true ->
        changes = Article.changeset(article, attrs)

        changes =
          if Ecto.Changeset.get_change(changes, :title),
            do:
              Ecto.Changeset.put_change(
                changes,
                :slug,
                slug(Ecto.Changeset.get_field(changes, :title), article.id)
              ),
            else: changes

        changes |> Ecto.Changeset.put_change(:revision, article.revision + 1) |> Repo.update()
    end
  end

  def publish(article) do
    if article.status == "published" do
      {:ok, article}
    else
      Repo.transaction(fn ->
        current = Repo.one!(from a in Article, where: a.id == ^article.id, lock: "FOR UPDATE")

        if current.status == "draft" do
          current
          |> Ecto.Changeset.change(
            status: "published",
            published_at: DateTime.utc_now(),
            revision: current.revision + 1
          )
          |> Repo.update!()
        else
          current
        end
      end)
    end
  end

  def list(params, viewer, mode \\ :all) do
    q = from(a in Article)

    q =
      case mode do
        :drafts ->
          from a in q, where: a.status == "draft" and a.author_id == ^viewer.id

        :feed ->
          from a in q,
            join: f in "follows",
            on: f.followed_id == a.author_id,
            where: f.follower_id == ^viewer.id and a.status == "published"

        _ ->
          from a in q, where: a.status == "published"
      end

    q =
      Enum.reduce(~w(tag author favorited), q, fn key, query ->
        filter(query, key, params[key])
      end)

    count = Repo.aggregate(q, :count, :id)

    articles =
      q
      |> order_by([a], desc: a.inserted_at, desc: a.id)
      |> limit(^number(params["limit"], 20))
      |> offset(^number(params["offset"], 0))
      |> Repo.all()

    %{articles: Enum.map(articles, &represent(&1, viewer, false)), articlesCount: count}
  end

  defp filter(q, _, nil), do: q
  defp filter(q, "tag", tag), do: from(a in q, where: ^tag in a.tag_list)

  defp filter(q, "author", username),
    do: from(a in q, join: u in User, on: u.id == a.author_id, where: u.username == ^username)

  defp filter(q, "favorited", username),
    do:
      from(a in q,
        join: f in "favorites",
        on: f.article_id == a.id,
        join: u in User,
        on: u.id == f.user_id,
        where: u.username == ^username
      )

  defp number(value, default) do
    case Integer.parse(to_string(value || default)) do
      {n, ""} when n >= 0 -> min(n, 1000)
      _ -> default
    end
  end

  def tags do
    Repo.all(from a in Article, where: a.status == "published", select: a.tag_list)
    |> List.flatten()
    |> Enum.uniq()
  end

  def represent(article, viewer, body? \\ true) do
    article = Repo.preload(article, :author)
    count = Repo.aggregate(from(f in "favorites", where: f.article_id == ^article.id), :count)

    favorited =
      if viewer,
        do:
          Repo.exists?(
            from f in "favorites", where: f.article_id == ^article.id and f.user_id == ^viewer.id
          ),
        else: false

    map = %{
      slug: article.slug,
      title: article.title,
      description: article.description,
      tagList: article.tag_list,
      createdAt: article.inserted_at,
      updatedAt: article.updated_at,
      favorited: favorited,
      favoritesCount: count,
      author: profile(article.author, viewer),
      status: article.status,
      publishedAt: article.published_at,
      revision: article.revision
    }

    if body?, do: Map.put(map, :body, article.body), else: map
  end

  def shared(article), do: Map.take(article, [:slug, :title, :body, :revision])

  def profile(user, viewer),
    do: %{
      username: user.username,
      bio: user.bio,
      image: user.image,
      following: Conduit.Accounts.following?(viewer, user)
    }

  def comment_create(article, viewer, attrs) when is_map(attrs) do
    if article.status == "draft" do
      {:error, %{article: ["is a draft"]}}
    else
      %Comment{article_id: article.id, author_id: viewer.id}
      |> Comment.changeset(attrs)
      |> Repo.insert()
    end
  end

  def comment_create(_, _, _), do: {:error, %{comment: ["is invalid"]}}

  def comments(article) do
    Repo.all(
      from c in Comment,
        where: c.article_id == ^article.id,
        order_by: [asc: c.id],
        preload: [:author]
    )
    |> Enum.map(&comment/1)
  end

  def comment(c),
    do: %{
      id: c.id,
      body: c.body,
      createdAt: c.inserted_at,
      updatedAt: c.updated_at,
      author: profile(Repo.preload(c, :author).author, nil)
    }

  def comment_delete(article, id, viewer) do
    with {id, ""} <- Integer.parse(id),
         %Comment{} = c <- Repo.get_by(Comment, id: id, article_id: article.id) do
      if c.author_id == viewer.id,
        do:
          (
            Repo.delete!(c)
            :ok
          ),
        else: {:forbidden, :comment}
    else
      _ -> {:not_found, :comment}
    end
  end

  def favorite(article, viewer, add?) do
    if article.status == "draft" do
      {:error, %{article: ["is a draft"]}}
    else
      if add? do
        Repo.insert_all("favorites", [%{article_id: article.id, user_id: viewer.id}],
          on_conflict: :nothing
        )
      else
        Repo.delete_all(
          from f in "favorites", where: f.article_id == ^article.id and f.user_id == ^viewer.id
        )
      end

      {:ok, article}
    end
  end

  def share_create(article) do
    key = random(32)
    revoke(article)

    share =
      %Share{article_id: article.id, public_id: random(18), key_hash: hash(key)} |> Repo.insert!()

    {:ok, %{id: share.public_id, key: key}}
  end

  def revoke(article) do
    case Repo.get_by(Share, article_id: article.id) do
      nil ->
        :ok

      share ->
        Repo.delete!(share)
        Conduit.Rooms.revoked(article.id)
        :ok
    end
  end

  def shared_article(id, key) do
    with true <- is_binary(key),
         %Share{} = share <- Repo.get_by(Share, public_id: id),
         true <- Plug.Crypto.secure_compare(share.key_hash, hash(key)),
         %Article{} = article <- Repo.get(Article, share.article_id) do
      {:ok, article}
    else
      _ -> {:not_found, :share}
    end
  end

  defp published_at("published"), do: DateTime.utc_now()
  defp published_at(_), do: nil

  defp slug(title, id),
    do:
      (title |> String.downcase() |> String.replace(~r/[^a-z0-9]+/, "-") |> String.trim("-")) <>
        "-#{id}"

  defp random(bytes), do: Base.url_encode64(:crypto.strong_rand_bytes(bytes), padding: false)
  defp hash(key), do: :crypto.hash(:sha256, key)
end

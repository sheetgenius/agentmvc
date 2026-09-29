defmodule Conduit.Shares do
  import Ecto.Query
  alias Conduit.Repo
  alias Conduit.Shares.Share
  alias Conduit.Articles

  def create(user, slug) do
    with {:ok, article} <- Articles.get_visible(slug, {:user, user}),
         :ok <- Articles.owner(article, user) do
      key = Base.url_encode64(:crypto.strong_rand_bytes(32), padding: false)
      id = Base.url_encode64(:crypto.strong_rand_bytes(16), padding: false)

      result =
        Repo.transaction(fn ->
          Repo.one!(
            from a in Conduit.Articles.Article, where: a.id == ^article.id, lock: "FOR UPDATE"
          )

          old =
            Repo.all(
              from s in Share,
                where: s.article_id == ^article.id and is_nil(s.revoked_at),
                select: s.public_id
            )

          Repo.update_all(
            from(s in Share, where: s.article_id == ^article.id and is_nil(s.revoked_at)),
            set: [revoked_at: DateTime.utc_now()]
          )

          {:ok, share} =
            Repo.insert(%Share{public_id: id, article_id: article.id, key_hash: digest(key)})

          {share, old}
        end)

      case result do
        {:ok, {_share, old}} ->
          Enum.each(old, &broadcast_revocation(article.id, &1))
          {:ok, %{id: id, key: key}}

        error ->
          error
      end
    end
  end

  def revoke(user, slug) do
    with {:ok, article} <- Articles.get_visible(slug, {:user, user}),
         :ok <- Articles.owner(article, user) do
      old =
        Repo.transaction(fn ->
          Repo.one!(
            from a in Conduit.Articles.Article, where: a.id == ^article.id, lock: "FOR UPDATE"
          )

          ids =
            Repo.all(
              from s in Share,
                where: s.article_id == ^article.id and is_nil(s.revoked_at),
                select: s.public_id
            )

          Repo.update_all(
            from(s in Share, where: s.article_id == ^article.id and is_nil(s.revoked_at)),
            set: [revoked_at: DateTime.utc_now()]
          )

          ids
        end)

      case old do
        {:ok, ids} ->
          Enum.each(ids, &broadcast_revocation(article.id, &1))
          :ok

        error ->
          error
      end
    end
  end

  def authorize(id, key) when is_binary(id) and is_binary(key) do
    case Repo.one(from s in Share, where: s.public_id == ^id and is_nil(s.revoked_at)) do
      %Share{} = share ->
        if secure_equal(share.key_hash, digest(key)), do: {:ok, share}, else: missing()

      _ ->
        missing()
    end
  end

  def authorize(_, _), do: missing()

  def article(id, key) do
    with {:ok, share} <- authorize(id, key),
         %Conduit.Articles.Article{} = article <-
           Repo.get(Conduit.Articles.Article, share.article_id) do
      {:ok, article}
    else
      _ -> missing()
    end
  end

  defp digest(key), do: :crypto.hash(:sha256, key)
  defp secure_equal(a, b), do: Plug.Crypto.secure_compare(a, b)
  defp missing, do: {:error, {:share, "not found"}}

  defp broadcast_revocation(article_id, share_id) do
    Phoenix.PubSub.broadcast(Conduit.PubSub, "article:#{article_id}", {:share_revoked, share_id})
  end
end

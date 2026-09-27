defmodule Conduit.Shares do
  import Ecto.Query
  alias Conduit.Content.{Article, Share}
  alias Conduit.Content
  alias Conduit.Repo

  def create(article, author) do
    with :ok <- author_only(article, author) do
      id = random_token(18)
      key = random_token(32)

      {:ok, old_id} =
        Repo.transaction(fn ->
          old_id = Repo.one(from s in Share, where: s.article_id == ^article.id, select: s.id)
          Repo.delete_all(from s in Share, where: s.article_id == ^article.id)

          %Share{}
          |> Share.changeset(%{id: id, key_hash: hash(key), article_id: article.id})
          |> Repo.insert!()

          old_id
        end)

      if old_id, do: Conduit.LiveRooms.revoke(old_id)
      {:ok, %{id: id, key: key}}
    end
  end

  def revoke(article, author) do
    with :ok <- author_only(article, author) do
      {_, old_ids} =
        Repo.delete_all(from s in Share, where: s.article_id == ^article.id, select: s.id)

      Enum.each(old_ids, &Conduit.LiveRooms.revoke/1)
      :ok
    end
  end

  def fetch(id, key) when is_binary(id) and is_binary(key) do
    case Repo.get(Share, id) do
      %Share{} = share ->
        if Plug.Crypto.secure_compare(share.key_hash, hash(key)) do
          {:ok, share, Repo.get!(Article, share.article_id)}
        else
          {:error, :share}
        end

      nil ->
        {:error, :share}
    end
  end

  def fetch(_, _), do: {:error, :share}

  def update(id, key, attrs) do
    Repo.transaction(fn ->
      query = from s in Share, where: s.id == ^id, lock: "FOR UPDATE"

      case Repo.one(query) do
        %Share{} = share when is_binary(key) ->
          if Plug.Crypto.secure_compare(share.key_hash, hash(key)) do
            article = Repo.get!(Article, share.article_id)

            case Article.check_shared_input(article, attrs) do
              :ok ->
                case Content.update_article(article, %{id: article.author_id}, attrs) do
                  {:ok, updated} -> updated
                  error -> Repo.rollback(error)
                end

              error ->
                Repo.rollback(error)
            end
          else
            Repo.rollback({:error, :share})
          end

        _ ->
          Repo.rollback({:error, :share})
      end
    end)
    |> case do
      {:ok, article} ->
        Conduit.LiveRooms.updated(article)
        {:ok, article}

      {:error, reason} ->
        reason
    end
  end

  def shared_article(article),
    do: %{
      slug: article.slug,
      title: article.title,
      body: article.body,
      revision: article.revision
    }

  defp author_only(article, %{id: id}) when article.author_id == id, do: :ok
  defp author_only(_, _), do: {:forbidden, :article}

  defp random_token(bytes),
    do: bytes |> :crypto.strong_rand_bytes() |> Base.url_encode64(padding: false)

  defp hash(key), do: :crypto.hash(:sha256, key)
end

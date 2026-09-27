defmodule ConduitWeb.ShareController do
  use ConduitWeb, :controller
  alias Conduit.{Content, Shares}

  action_fallback ConduitWeb.FallbackController

  def create(conn, %{"slug" => slug}) do
    with {:ok, article} <- Content.fetch_article(slug, conn.assigns.current_user),
         {:ok, share} <- Shares.create(article, conn.assigns.current_user) do
      conn |> put_status(:created) |> json(%{share: share})
    end
  end

  def delete(conn, %{"slug" => slug}) do
    with {:ok, article} <- Content.fetch_article(slug, conn.assigns.current_user),
         :ok <- Shares.revoke(article, conn.assigns.current_user) do
      send_resp(conn, :no_content, "")
    end
  end

  def show_article(conn, %{"id" => id}) do
    with {:ok, _share, article} <- Shares.fetch(id, key(conn)) do
      json(conn, %{article: Shares.shared_article(article)})
    end
  end

  def update_article(conn, %{"id" => id}) do
    with {:ok, article} <- Shares.update(id, key(conn), article_attrs(conn.body_params)) do
      json(conn, %{article: Shares.shared_article(article)})
    else
      {:stale, article} ->
        conn
        |> put_status(:conflict)
        |> json(%{errors: %{revision: ["is stale"]}, article: Shares.shared_article(article)})

      error ->
        error
    end
  end

  defp key(conn), do: conn |> get_req_header("x-share-key") |> List.first()

  defp article_attrs(%{"article" => attrs} = body) when map_size(body) == 1, do: attrs
  defp article_attrs(_), do: nil
end

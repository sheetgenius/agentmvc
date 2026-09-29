defmodule ConduitWeb.ShareController do
  use ConduitWeb, :controller
  alias ConduitWeb.API
  alias Conduit.{Articles, Shares}

  def create(conn, %{"slug" => slug}) do
    with {:ok, user} <- API.user(conn),
         {:ok, share} <- Shares.create(user, slug) do
      API.reply(conn, 201, %{share: share})
    else
      {:error, reason} -> API.error(conn, reason)
    end
  end

  def delete(conn, %{"slug" => slug}) do
    with {:ok, user} <- API.user(conn), :ok <- Shares.revoke(user, slug) do
      API.no_content(conn)
    else
      {:error, reason} -> API.error(conn, reason)
    end
  end

  def show_article(conn, %{"id" => id}) do
    with {:ok, article} <- Shares.article(id, key(conn)) do
      API.reply(conn, 200, %{article: Articles.shared(article)})
    else
      {:error, reason} -> API.error(conn, reason)
    end
  end

  def update_article(conn, %{"id" => id} = params) do
    key = key(conn)

    with {:ok, _share} <- Shares.authorize(id, key),
         {:ok, attrs} <- API.object(params, "article"),
         {:ok, article} <- Articles.commit({:share, id, key}, attrs) do
      API.reply(conn, 200, %{article: Articles.shared(article)})
    else
      {:error, {:stale, article}} -> API.error(conn, {:stale_shared, article})
      {:error, reason} -> API.error(conn, reason)
    end
  end

  def live(conn, %{"id" => id}),
    do:
      conn |> WebSockAdapter.upgrade(Conduit.Live.Socket, id, timeout: 60_000) |> Plug.Conn.halt()

  defp key(conn), do: conn |> Plug.Conn.get_req_header("x-share-key") |> List.first()
end

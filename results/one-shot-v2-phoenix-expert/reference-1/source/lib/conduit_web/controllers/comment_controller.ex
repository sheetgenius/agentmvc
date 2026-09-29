defmodule ConduitWeb.CommentController do
  use ConduitWeb, :controller
  alias ConduitWeb.API
  alias Conduit.Articles

  def index(conn, %{"slug" => slug}) do
    with {:ok, article} <- Articles.get_published(slug, API.caller(conn)) do
      API.reply(conn, 200, %{comments: Articles.comments(article, API.caller(conn))})
    else
      {:error, reason} -> API.error(conn, reason)
    end
  end

  def create(conn, %{"slug" => slug} = params) do
    with {:ok, user} <- API.user(conn),
         {:ok, article} <- Articles.get_visible(slug, {:user, user}),
         :ok <- Articles.ensure_published(article),
         {:ok, attrs} <- API.object(params, "comment"),
         {:ok, comment} <- Articles.create_comment(user, article, attrs) do
      API.reply(conn, 201, %{comment: hd(Articles.present_comments([comment], {:user, user}))})
    else
      {:error, reason} -> API.error(conn, reason)
    end
  end

  def delete(conn, %{"slug" => slug, "id" => id}) do
    with {:ok, user} <- API.user(conn),
         {:ok, article} <- Articles.get_published(slug, {:user, user}),
         {:ok, _} <- Articles.delete_comment(user, article, id) do
      API.no_content(conn)
    else
      {:error, reason} -> API.error(conn, reason)
    end
  end
end

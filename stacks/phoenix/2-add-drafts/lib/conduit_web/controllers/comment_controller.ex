defmodule ConduitWeb.CommentController do
  use ConduitWeb, :controller
  alias Conduit.Content
  alias ConduitWeb.Presenter

  action_fallback ConduitWeb.FallbackController

  def index(conn, %{"slug" => slug}) do
    with {:ok, article} <- Content.fetch_article(slug, conn.assigns.current_user) do
      comments = Content.list_comments(article)

      json(conn, %{
        comments: Enum.map(comments, &Presenter.comment(&1, conn.assigns.current_user))
      })
    end
  end

  def create(conn, %{"slug" => slug, "comment" => attrs}) do
    with {:ok, article} <- Content.fetch_article(slug, conn.assigns.current_user),
         {:ok, comment} <- Content.create_comment(article, conn.assigns.current_user, attrs) do
      conn
      |> put_status(:created)
      |> json(%{comment: Presenter.comment(comment, conn.assigns.current_user)})
    end
  end

  def delete(conn, %{"slug" => slug, "id" => id}) do
    with {:ok, article} <- Content.fetch_article(slug, conn.assigns.current_user),
         {:ok, comment} <- find_comment(article, id),
         :ok <- owner(comment, conn.assigns.current_user),
         {:ok, _} <- Content.delete_comment(comment) do
      send_resp(conn, :no_content, "")
    end
  end

  defp find_comment(article, id) do
    with {id, ""} <- Integer.parse(id),
         %{} = comment <- Content.get_comment(article, id) do
      {:ok, comment}
    else
      _ -> {:error, :comment}
    end
  end

  defp owner(comment, user) when comment.author_id == user.id, do: :ok
  defp owner(_, _), do: {:forbidden, :comment}
end

defmodule ConduitWeb.ExportController do
  use ConduitWeb, :controller
  alias Conduit.Exports

  action_fallback ConduitWeb.FallbackController

  def create(conn, _params) do
    with {:ok, export} <- Exports.create(conn.assigns.current_user) do
      conn |> put_status(:accepted) |> json(%{export: present(export)})
    end
  end

  def show(conn, %{"id" => id}) do
    with {:ok, export} <- Exports.get(conn.assigns.current_user, id) do
      json(conn, %{export: present(export)})
    end
  end

  defp present(export) do
    %{
      id: export.id,
      status: export.status,
      createdAt: export.inserted_at,
      completedAt: export.completed_at,
      articles: export.articles
    }
  end
end

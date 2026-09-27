defmodule ConduitWeb.Auth do
  import Plug.Conn
  alias Conduit.Accounts

  def init(action), do: action
  def call(conn, :fetch_user), do: fetch_user(conn)
  def call(conn, :require_user), do: require_user(conn)

  defp fetch_user(conn) do
    case get_req_header(conn, "authorization") do
      ["Token " <> token] ->
        case Accounts.from_token(token) do
          {:ok, user} -> assign(conn, :current_user, user)
          _ -> reject(conn, "is invalid")
        end

      [] ->
        assign(conn, :current_user, nil)

      _ ->
        reject(conn, "is invalid")
    end
  end

  defp require_user(%{assigns: %{current_user: nil}} = conn), do: reject(conn, "is missing")
  defp require_user(conn), do: conn

  defp reject(conn, message) do
    conn
    |> put_resp_content_type("application/json")
    |> send_resp(401, Jason.encode!(%{errors: %{token: [message]}}))
    |> halt()
  end
end

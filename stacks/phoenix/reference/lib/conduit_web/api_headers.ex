defmodule ConduitWeb.ApiHeaders do
  import Plug.Conn
  def init(opts), do: opts

  def call(conn, _) do
    conn
    |> put_resp_header("x-content-type-options", "nosniff")
    |> put_resp_header("access-control-allow-origin", "*")
    |> put_resp_header("access-control-allow-headers", "authorization, content-type, x-share-key")
    |> put_resp_header("access-control-allow-methods", "GET, POST, PUT, DELETE, OPTIONS")
  end
end

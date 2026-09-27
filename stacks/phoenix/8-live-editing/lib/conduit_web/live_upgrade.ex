defmodule ConduitWeb.LiveUpgrade do
  import Plug.Conn

  def init(opts), do: opts

  def call(%{method: "GET", path_info: ["api", "shares", id, "live"]} = conn, _opts) do
    conn
    |> WebSockAdapter.upgrade(ConduitWeb.ShareSocket, id,
      max_frame_size: 16_384,
      timeout: :infinity
    )
    |> halt()
  end

  def call(conn, _opts), do: conn
end

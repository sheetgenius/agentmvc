defmodule ConduitWeb.Plugs.Caller do
  import Plug.Conn

  def init(opts), do: opts

  def call(conn, _opts) do
    token = conn |> get_req_header("authorization") |> List.first()
    assign(conn, :caller, Conduit.Accounts.caller(token))
  end
end

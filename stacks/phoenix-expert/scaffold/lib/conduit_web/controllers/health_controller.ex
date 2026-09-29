defmodule ConduitWeb.HealthController do
  use ConduitWeb, :controller

  def show(conn, _params), do: json(conn, %{status: "ok"})
end

defmodule ConduitWeb.Endpoint do
  use Phoenix.Endpoint, otp_app: :conduit

  plug Plug.RequestId
  plug Plug.Telemetry, event_prefix: [:phoenix, :endpoint]
  plug CORSPlug, credentials: false
  plug ConduitWeb.LiveUpgrade
  plug Plug.Parsers, parsers: [:json], pass: ["*/*"], json_decoder: Phoenix.json_library()
  plug Plug.Head
  plug ConduitWeb.Router
end

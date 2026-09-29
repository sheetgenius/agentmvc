import Config

port = String.to_integer(System.get_env("PORT", "4108"))

config :conduit, ConduitWeb.Endpoint, http: [ip: {0, 0, 0, 0}, port: port]

if config_env() == :prod do
  config :conduit, Conduit.Repo,
    url: System.fetch_env!("DATABASE_URL"),
    pool_size: 10

  config :conduit, ConduitWeb.Endpoint,
    server: true,
    secret_key_base: System.fetch_env!("SECRET_KEY_BASE")
end

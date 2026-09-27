import Config

if System.get_env("PHX_SERVER"), do: config(:conduit, ConduitWeb.Endpoint, server: true)

config :conduit, ConduitWeb.Endpoint,
  http: [port: String.to_integer(System.get_env("PORT", "4102"))]

if config_env() == :prod do
  config :conduit, Conduit.Repo,
    url: System.fetch_env!("DATABASE_URL"),
    pool_size: String.to_integer(System.get_env("POOL_SIZE", "10"))

  config :conduit, ConduitWeb.Endpoint,
    url: [host: System.get_env("PHX_HOST", "localhost")],
    http: [ip: {0, 0, 0, 0}],
    secret_key_base: System.fetch_env!("SECRET_KEY_BASE")
end

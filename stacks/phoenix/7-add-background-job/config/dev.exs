import Config

config :conduit, Conduit.Repo,
  username: "postgres",
  password: "postgres",
  hostname: System.get_env("DB_HOST", "localhost"),
  database: "conduit_dev"

config :conduit, ConduitWeb.Endpoint,
  http: [ip: {0, 0, 0, 0}],
  secret_key_base: "2i2dy1+QF/cY7hnwNJaJaWKITqCdCDfn5uT30c1NFkhQAIiogFqB320LghaIP1Jj"

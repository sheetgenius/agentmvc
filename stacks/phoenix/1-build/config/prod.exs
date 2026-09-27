import Config

config :conduit, ConduitWeb.Endpoint, force_ssl: [rewrite_on: [:x_forwarded_proto]]
config :logger, level: :info

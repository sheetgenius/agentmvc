import Config

config :conduit, ecto_repos: [Conduit.Repo]
config :conduit, Oban, repo: Conduit.Repo, queues: [exports: 2]

config :conduit, ConduitWeb.Endpoint,
  adapter: Bandit.PhoenixAdapter,
  render_errors: [formats: [json: ConduitWeb.ErrorJSON], layout: false]

config :phoenix, :json_library, Jason
import_config "#{config_env()}.exs"

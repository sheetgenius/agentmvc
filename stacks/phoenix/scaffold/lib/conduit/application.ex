defmodule Conduit.Application do
  # See https://elixir.hexdocs.pm/Application.html
  # for more information on OTP Applications
  @moduledoc false

  use Application

  @impl true
  def start(_type, _args) do
    children = [
      ConduitWeb.Telemetry,
      Conduit.Repo,
      {DNSCluster, query: Application.get_env(:conduit, :dns_cluster_query) || :ignore},
      {Phoenix.PubSub, name: Conduit.PubSub},
      # Start a worker by calling: Conduit.Worker.start_link(arg)
      # {Conduit.Worker, arg},
      # Start to serve requests, typically the last entry
      ConduitWeb.Endpoint
    ]

    # See https://elixir.hexdocs.pm/Supervisor.html
    # for other strategies and supported options
    opts = [strategy: :one_for_one, name: Conduit.Supervisor]
    Supervisor.start_link(children, opts)
  end

  # Tell Phoenix to update the endpoint configuration
  # whenever the application is updated.
  @impl true
  def config_change(changed, _new, removed) do
    ConduitWeb.Endpoint.config_change(changed, removed)
    :ok
  end
end

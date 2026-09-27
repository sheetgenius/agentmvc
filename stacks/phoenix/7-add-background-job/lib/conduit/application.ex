defmodule Conduit.Application do
  @moduledoc false
  use Application

  @impl true
  def start(_type, _args) do
    Supervisor.start_link(
      [
        Conduit.Repo,
        {Oban, Application.fetch_env!(:conduit, Oban)},
        ConduitWeb.LoginLimiter,
        ConduitWeb.Endpoint
      ],
      strategy: :one_for_one,
      name: Conduit.Supervisor
    )
  end

  @impl true
  def config_change(changed, _new, removed) do
    ConduitWeb.Endpoint.config_change(changed, removed)
    :ok
  end
end

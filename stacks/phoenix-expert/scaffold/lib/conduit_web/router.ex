defmodule ConduitWeb.Router do
  use ConduitWeb, :router

  pipeline :api do
    plug :accepts, ["json"]
  end

  scope "/", ConduitWeb do
    pipe_through :api
    get "/health", HealthController, :show
  end

  scope "/api", ConduitWeb do
    pipe_through :api
  end
end

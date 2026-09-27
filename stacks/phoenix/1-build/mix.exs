defmodule Conduit.MixProject do
  use Mix.Project

  def project do
    [
      app: :conduit,
      version: "0.1.0",
      elixir: "~> 1.17",
      start_permanent: Mix.env() == :prod,
      deps: deps()
    ]
  end

  def application, do: [mod: {Conduit.Application, []}, extra_applications: [:logger]]

  defp deps do
    [
      {:phoenix, "~> 1.8.15"},
      {:ecto_sql, "~> 3.13"},
      {:postgrex, ">= 0.0.0"},
      {:jason, "~> 1.2"},
      {:bandit, "~> 1.5"},
      {:bcrypt_elixir, "~> 3.2"},
      {:joken, "~> 2.6"},
      {:cors_plug, "~> 3.0"}
    ]
  end
end

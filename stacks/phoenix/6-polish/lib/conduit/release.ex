defmodule Conduit.Release do
  @moduledoc false

  def migrate do
    Application.load(:conduit)

    for repo <- Application.fetch_env!(:conduit, :ecto_repos) do
      {:ok, _, _} = Ecto.Migrator.with_repo(repo, &Ecto.Migrator.run(&1, :up, all: true))
    end
  end
end

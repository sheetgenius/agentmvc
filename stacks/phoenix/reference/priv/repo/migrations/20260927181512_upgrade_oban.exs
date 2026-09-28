defmodule Conduit.Repo.Migrations.UpgradeOban do
  use Ecto.Migration

  def change do
    Oban.Migration.up(version: 14)
  end
end

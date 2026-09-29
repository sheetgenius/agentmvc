defmodule Conduit.Exports.Export do
  use Ecto.Schema

  schema "exports" do
    belongs_to :user, Conduit.Accounts.User
    field :status, :string, default: "pending"
    field :articles, {:array, :map}
    field :completed_at, :utc_datetime_usec
    timestamps(type: :utc_datetime_usec)
  end
end

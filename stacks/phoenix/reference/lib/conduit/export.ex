defmodule Conduit.Export do
  use Ecto.Schema

  schema "exports" do
    field :status, :string, default: "pending"
    field :articles, :map
    field :completed_at, :utc_datetime_usec
    belongs_to :user, Conduit.User
    timestamps(type: :utc_datetime_usec)
  end
end

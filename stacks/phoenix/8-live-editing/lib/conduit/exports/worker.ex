defmodule Conduit.Exports.Worker do
  use Oban.Worker, queue: :exports

  @impl true
  def perform(%Oban.Job{args: %{"export_id" => id}}), do: Conduit.Exports.complete(id)
end

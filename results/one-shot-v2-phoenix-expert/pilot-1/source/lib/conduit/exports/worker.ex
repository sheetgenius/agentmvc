defmodule Conduit.Exports.Worker do
  use Oban.Worker, queue: :exports, max_attempts: 10

  @impl Oban.Worker
  def perform(%Oban.Job{args: %{"export_id" => id}}) do
    case Conduit.Exports.complete(id) do
      {:ok, _} -> :ok
      error -> error
    end
  end
end

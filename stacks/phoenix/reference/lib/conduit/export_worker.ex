defmodule Conduit.ExportWorker do
  use Oban.Worker, queue: :exports

  def perform(%Oban.Job{args: %{"export_id" => id}}),
    do:
      (
        Conduit.Exports.run(id)
        :ok
      )
end

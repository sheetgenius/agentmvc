defmodule ConduitWeb.LiveSocket do
  @behaviour WebSock
  alias Conduit.{Content, Rooms}

  def init(id) do
    Process.send_after(self(), :subscribe_timeout, 5_000)
    {:ok, %{id: id, article_id: nil, revision: 0}}
  end

  def handle_in({payload, opcode: :text}, %{article_id: nil} = state) do
    case Jason.decode(payload) do
      {:ok, %{"type" => "subscribe", "key" => key}} ->
        case Rooms.join(state.id, key, self()) do
          {:ok, article, count} ->
            {:push, frame(%{type: "ready", article: Content.shared(article), presence: count}),
             %{state | article_id: article.id, revision: article.revision}}

          :full ->
            stop(%{type: "room_full", limit: 100}, state)

          :invalid ->
            stop(%{type: "invalid_link"}, state)
        end

      _ ->
        stop(%{type: "invalid_link"}, state)
    end
  end

  def handle_in(_, state), do: {:ok, state}
  def handle_info(:subscribe_timeout, %{article_id: nil} = state), do: {:stop, :normal, state}
  def handle_info(:subscribe_timeout, state), do: {:ok, state}

  def handle_info({:presence, count}, state),
    do: {:push, frame(%{type: "presence", count: count}), state}

  def handle_info({:updated, article}, state) do
    if article.revision > state.revision,
      do:
        {:push, frame(%{type: "updated", article: article}),
         %{state | revision: article.revision}},
      else: {:ok, state}
  end

  def handle_info(:revoked, state), do: stop(%{type: "revoked"}, state)
  def handle_info(_, state), do: {:ok, state}
  def terminate(_, %{article_id: id}) when not is_nil(id), do: Rooms.leave(id, self())
  def terminate(_, _), do: :ok
  defp frame(value), do: {:text, Jason.encode!(value)}
  defp stop(value, state), do: {:stop, :normal, 1000, frame(value), state}
end

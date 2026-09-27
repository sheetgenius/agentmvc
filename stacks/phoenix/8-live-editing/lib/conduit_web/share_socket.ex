defmodule ConduitWeb.ShareSocket do
  @behaviour WebSock
  alias Conduit.LiveRooms

  @impl true
  def init(id) do
    Process.send_after(self(), :subscribe_timeout, 5_000)
    {:ok, %{id: id, subscribed: false, revision: 0}}
  end

  @impl true
  def handle_in({payload, [opcode: :text]}, %{subscribed: false} = state) do
    case Jason.decode(payload) do
      {:ok, %{"type" => "subscribe", "key" => key}} ->
        case LiveRooms.join(state.id, key) do
          {:ok, article, count} ->
            {:push, json(%{type: "ready", article: article, presence: count}),
             %{state | subscribed: true, revision: article.revision}}

          {:error, :room_full} ->
            close(%{type: "room_full", limit: 100}, state)

          _ ->
            close(%{type: "invalid_link"}, state)
        end

      _ ->
        close(%{type: "invalid_link"}, state)
    end
  end

  def handle_in(_, %{subscribed: false} = state), do: close(%{type: "invalid_link"}, state)
  def handle_in(_, state), do: {:ok, state}

  @impl true
  def handle_info(:subscribe_timeout, %{subscribed: false} = state), do: {:stop, :normal, state}
  def handle_info(:subscribe_timeout, state), do: {:ok, state}

  def handle_info({:updated, article}, state) when article.revision > state.revision do
    {:push, json(%{type: "updated", article: article}), %{state | revision: article.revision}}
  end

  def handle_info({:updated, _}, state), do: {:ok, state}

  def handle_info({:presence, count}, state),
    do: {:push, json(%{type: "presence", count: count}), state}

  def handle_info(:revoked, state), do: close(%{type: "revoked"}, state)

  @impl true
  def terminate(_reason, %{subscribed: true, id: id}), do: LiveRooms.leave(id)
  def terminate(_reason, _state), do: :ok

  defp json(message), do: {:text, Jason.encode!(message)}
  defp close(message, state), do: {:stop, :normal, 1000, json(message), state}
end

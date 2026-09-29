defmodule Conduit.Live.Socket do
  @behaviour WebSock
  alias Conduit.Live.Room

  @impl WebSock
  def init(share_id) do
    Process.send_after(self(), :subscription_timeout, 5_000)
    {:ok, %{share_id: share_id, article_id: nil, revision: 0, admitted: false}}
  end

  @impl WebSock
  def handle_in({payload, [opcode: :text]}, %{admitted: false} = state) do
    with {:ok, %{"type" => "subscribe", "key" => key}} <- Jason.decode(payload),
         {:ok, share} <- Conduit.Shares.authorize(state.share_id, key),
         {:ok, article, count} <- Room.join(share.article_id, state.share_id, key, self()) do
      {:push, frame(%{type: "ready", article: article, presence: count}),
       %{state | admitted: true, article_id: share.article_id, revision: article.revision}}
    else
      {:error, :room_full} -> close(%{type: "room_full", limit: 100}, state)
      _ -> close(%{type: "invalid_link"}, state)
    end
  end

  def handle_in(_frame, state), do: {:ok, state}

  @impl WebSock
  def handle_info(:subscription_timeout, %{admitted: false} = state), do: {:stop, :normal, state}
  def handle_info(:subscription_timeout, state), do: {:ok, state}

  def handle_info({:room_updated, %{revision: revision} = article}, state)
      when revision > state.revision do
    {:push, frame(%{type: "updated", article: article}), %{state | revision: revision}}
  end

  def handle_info({:room_updated, _}, state), do: {:ok, state}

  def handle_info({:room_presence, count}, state),
    do: {:push, frame(%{type: "presence", count: count}), state}

  def handle_info(:room_revoked, state), do: close(%{type: "revoked"}, state)
  def handle_info(_, state), do: {:ok, state}

  defp frame(value), do: {:text, Jason.encode!(value)}
  defp close(value, state), do: {:stop, :normal, 1000, frame(value), state}
end

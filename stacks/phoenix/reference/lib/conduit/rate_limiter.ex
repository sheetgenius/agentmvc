defmodule Conduit.RateLimiter do
  use GenServer
  def start_link(_), do: GenServer.start_link(__MODULE__, %{}, name: __MODULE__)
  def init(state), do: {:ok, state}
  def failed(email), do: GenServer.call(__MODULE__, {:failed, email})
  def reset(email), do: GenServer.cast(__MODULE__, {:reset, email})

  def handle_call({:failed, email}, _, state) do
    now = System.monotonic_time(:second)

    {count, started} =
      case Map.get(state, email) do
        {n, start} when now - start < 60 -> {n + 1, start}
        _ -> {1, now}
      end

    {:reply, count > 10, Map.put(state, email, {count, started})}
  end

  def handle_cast({:reset, email}, state), do: {:noreply, Map.delete(state, email)}
end

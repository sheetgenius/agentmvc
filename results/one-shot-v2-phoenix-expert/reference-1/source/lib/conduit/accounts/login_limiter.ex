defmodule Conduit.Accounts.LoginLimiter do
  use GenServer

  @window_ms 15 * 60 * 1_000
  @max_failures 20

  def start_link(_), do: GenServer.start_link(__MODULE__, :ok, name: __MODULE__)
  def allowed?(email), do: GenServer.call(__MODULE__, {:allowed?, email})
  def failed(email), do: GenServer.call(__MODULE__, {:failed, email})
  def clear(email), do: GenServer.call(__MODULE__, {:clear, email})
  def dummy_hash, do: GenServer.call(__MODULE__, :dummy_hash)

  @impl GenServer
  def init(:ok) do
    Process.send_after(self(), :purge, @window_ms)
    {:ok, %{failures: %{}, dummy_hash: Bcrypt.hash_pwd_salt("unmatched-password")}}
  end

  @impl GenServer
  def handle_call({:allowed?, email}, _from, state) do
    now = System.monotonic_time(:millisecond)
    failures = forget_expired(state.failures, email, now)

    allowed =
      case Map.get(failures, email) do
        {count, _started} when count >= @max_failures -> false
        _ -> true
      end

    {:reply, allowed, %{state | failures: failures}}
  end

  def handle_call({:failed, email}, _from, state) do
    now = System.monotonic_time(:millisecond)
    failures = forget_expired(state.failures, email, now)
    {count, started} = Map.get(failures, email, {0, now})
    {:reply, :ok, %{state | failures: Map.put(failures, email, {count + 1, started})}}
  end

  def handle_call({:clear, email}, _from, state),
    do: {:reply, :ok, %{state | failures: Map.delete(state.failures, email)}}

  def handle_call(:dummy_hash, _from, state), do: {:reply, state.dummy_hash, state}

  @impl GenServer
  def handle_info(:purge, state) do
    now = System.monotonic_time(:millisecond)

    failures =
      Map.filter(state.failures, fn {_email, {_count, started}} -> now - started < @window_ms end)

    Process.send_after(self(), :purge, @window_ms)
    {:noreply, %{state | failures: failures}}
  end

  defp forget_expired(failures, email, now) do
    case Map.get(failures, email) do
      {_count, started} when now - started >= @window_ms -> Map.delete(failures, email)
      _ -> failures
    end
  end
end

defmodule Conduit.Accounts.LoginLimiter do
  use GenServer

  @window_ms 15 * 60 * 1_000
  @max_failures 20

  def start_link(_), do: GenServer.start_link(__MODULE__, :ok, name: __MODULE__)
  def reserve(email), do: GenServer.call(__MODULE__, {:reserve, email})

  def finish(reservation, outcome),
    do: GenServer.call(__MODULE__, {:finish, reservation, outcome})

  def cancel(reservation), do: GenServer.call(__MODULE__, {:cancel, reservation})
  def dummy_hash, do: GenServer.call(__MODULE__, :dummy_hash)

  def with_reservation(email, fun) do
    case reserve(email) do
      {:ok, reservation} ->
        try do
          fun.(reservation)
        after
          cancel(reservation)
        end

      :rate_limited ->
        {:error, :rate_limited}
    end
  end

  @impl GenServer
  def init(:ok) do
    Process.send_after(self(), :purge, @window_ms)

    {:ok,
     %{
       failures: %{},
       pending: %{},
       reservations: %{},
       dummy_hash: Bcrypt.hash_pwd_salt("unmatched-password")
     }}
  end

  @impl GenServer
  def handle_call({:reserve, email}, {caller, _}, state) do
    now = System.monotonic_time(:millisecond)
    failures = forget_expired(state.failures, email, now)
    {failed, _started} = Map.get(failures, email, {0, now})

    if failed + Map.get(state.pending, email, 0) >= @max_failures do
      {:reply, :rate_limited, %{state | failures: failures}}
    else
      reservation = Process.monitor(caller)

      {:reply, {:ok, reservation},
       %{
         state
         | failures: failures,
           pending: Map.update(state.pending, email, 1, &(&1 + 1)),
           reservations: Map.put(state.reservations, reservation, email)
       }}
    end
  end

  def handle_call({:finish, reservation, outcome}, _from, state)
      when outcome in [:failed, :success] do
    case release(state, reservation) do
      {:ok, email, state} ->
        failures =
          case outcome do
            :success ->
              Map.delete(state.failures, email)

            :failed ->
              now = System.monotonic_time(:millisecond)
              failures = forget_expired(state.failures, email, now)
              {count, started} = Map.get(failures, email, {0, now})
              Map.put(failures, email, {count + 1, started})
          end

        {:reply, :ok, %{state | failures: failures}}

      :missing ->
        {:reply, :expired, state}
    end
  end

  def handle_call({:cancel, reservation}, _from, state) do
    state =
      case release(state, reservation) do
        {:ok, _email, state} -> state
        :missing -> state
      end

    {:reply, :ok, state}
  end

  def handle_call(:dummy_hash, _from, state), do: {:reply, state.dummy_hash, state}

  @impl GenServer
  def handle_info({:DOWN, reservation, :process, _caller, _reason}, state) do
    case release(state, reservation) do
      {:ok, _email, state} -> {:noreply, state}
      :missing -> {:noreply, state}
    end
  end

  def handle_info(:purge, state) do
    now = System.monotonic_time(:millisecond)

    failures =
      Map.filter(state.failures, fn {_email, {_count, started}} -> now - started < @window_ms end)

    Process.send_after(self(), :purge, @window_ms)
    {:noreply, %{state | failures: failures}}
  end

  defp release(state, reservation) do
    case Map.pop(state.reservations, reservation) do
      {nil, _reservations} ->
        :missing

      {email, reservations} ->
        Process.demonitor(reservation, [:flush])

        pending =
          case Map.fetch!(state.pending, email) do
            1 -> Map.delete(state.pending, email)
            count -> Map.put(state.pending, email, count - 1)
          end

        {:ok, email, %{state | pending: pending, reservations: reservations}}
    end
  end

  defp forget_expired(failures, email, now) do
    case Map.get(failures, email) do
      {_count, started} when now - started >= @window_ms -> Map.delete(failures, email)
      _ -> failures
    end
  end
end

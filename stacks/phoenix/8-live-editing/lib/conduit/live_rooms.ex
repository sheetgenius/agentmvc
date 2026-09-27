defmodule Conduit.LiveRooms do
  use GenServer
  alias Conduit.Shares

  @limit 100

  def start_link(_), do: GenServer.start_link(__MODULE__, %{}, name: __MODULE__)

  def join(id, key), do: GenServer.call(__MODULE__, {:join, id, key})
  def leave(id), do: GenServer.cast(__MODULE__, {:leave, id, self()})
  def revoke(id), do: GenServer.cast(__MODULE__, {:revoke, id})
  def updated(article), do: GenServer.cast(__MODULE__, {:updated, article})

  @impl true
  def init(_), do: {:ok, %{rooms: %{}, monitors: %{}}}

  @impl true
  def handle_call({:join, id, key}, {pid, _}, state) do
    with {:ok, _share, article} <- Shares.fetch(id, key) do
      room = Map.get(state.rooms, id, MapSet.new())

      if MapSet.size(room) == @limit do
        {:reply, {:error, :room_full}, state}
      else
        ref = Process.monitor(pid)
        count = MapSet.size(room) + 1
        Enum.each(room, &send(&1, {:presence, count}))

        state = %{
          state
          | rooms: Map.put(state.rooms, id, MapSet.put(room, pid)),
            monitors: Map.put(state.monitors, ref, {id, pid})
        }

        {:reply, {:ok, Shares.shared_article(article), count}, state}
      end
    else
      error -> {:reply, error, state}
    end
  end

  @impl true
  def handle_cast({:updated, article}, state) do
    case Conduit.Repo.get_by(Conduit.Content.Share, article_id: article.id) do
      nil -> :ok
      share -> each_member(state, share.id, {:updated, Shares.shared_article(article)})
    end

    {:noreply, state}
  end

  def handle_cast({:revoke, id}, state) do
    each_member(state, id, :revoked)
    {:noreply, clear_room(state, id)}
  end

  def handle_cast({:leave, id, pid}, state), do: {:noreply, remove_member(state, id, pid)}

  @impl true
  def handle_info({:DOWN, ref, :process, _pid, _reason}, state) do
    case Map.get(state.monitors, ref) do
      {id, pid} -> {:noreply, remove_member(state, id, pid)}
      nil -> {:noreply, state}
    end
  end

  defp remove_member(state, id, pid) do
    room = Map.get(state.rooms, id, MapSet.new())

    if MapSet.member?(room, pid) do
      room = MapSet.delete(room, pid)
      refs = for {ref, {^id, ^pid}} <- state.monitors, do: ref
      Enum.each(refs, &Process.demonitor(&1, [:flush]))
      monitors = Map.drop(state.monitors, refs)
      Enum.each(room, &send(&1, {:presence, MapSet.size(room)}))

      rooms =
        if MapSet.size(room) == 0,
          do: Map.delete(state.rooms, id),
          else: Map.put(state.rooms, id, room)

      %{state | rooms: rooms, monitors: monitors}
    else
      state
    end
  end

  defp clear_room(state, id) do
    refs = for {ref, {share_id, _}} <- state.monitors, share_id == id, do: ref
    Enum.each(refs, &Process.demonitor(&1, [:flush]))
    %{state | rooms: Map.delete(state.rooms, id), monitors: Map.drop(state.monitors, refs)}
  end

  defp each_member(state, id, message) do
    state.rooms |> Map.get(id, MapSet.new()) |> Enum.each(&send(&1, message))
  end
end

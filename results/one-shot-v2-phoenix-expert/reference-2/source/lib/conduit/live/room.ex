defmodule Conduit.Live.Room do
  use GenServer
  alias Conduit.Articles
  alias Conduit.Shares
  alias Conduit.Repo

  @limit 100

  def child_spec(article_id) do
    %{
      id: {__MODULE__, article_id},
      start: {__MODULE__, :start_link, [article_id]},
      restart: :temporary
    }
  end

  def start_link(article_id) do
    GenServer.start_link(__MODULE__, article_id, name: via(article_id))
  end

  def join(article_id, share_id, key, socket) do
    with {:ok, room} <- ensure_room(article_id) do
      GenServer.call(room, {:join, share_id, key, socket}, 15_000)
    end
  end

  defp ensure_room(article_id) do
    case Registry.lookup(Conduit.RoomRegistry, article_id) do
      [{pid, _}] ->
        {:ok, pid}

      [] ->
        case DynamicSupervisor.start_child(Conduit.RoomSupervisor, {__MODULE__, article_id}) do
          {:ok, pid} -> {:ok, pid}
          {:error, {:already_started, pid}} -> {:ok, pid}
          other -> other
        end
    end
  end

  defp via(article_id), do: {:via, Registry, {Conduit.RoomRegistry, article_id}}

  @impl GenServer
  def init(article_id) do
    Phoenix.PubSub.subscribe(Conduit.PubSub, "article:#{article_id}")
    {:ok, %{article_id: article_id, members: %{}, revision: 0}}
  end

  @impl GenServer
  def handle_call({:join, share_id, key, socket}, _from, state) do
    case Shares.authorize(share_id, key) do
      {:ok, %{article_id: id}} when id == state.article_id ->
        if map_size(state.members) >= @limit,
          do: {:reply, {:error, :room_full}, state},
          else: admit(share_id, key, socket, state)

      _ ->
        {:reply, {:error, :invalid_link}, state}
    end
  end

  defp admit(share_id, key, socket, state) do
    with {:ok, %{article_id: id}} when id == state.article_id <- Shares.authorize(share_id, key),
         article when not is_nil(article) <- Repo.get(Conduit.Articles.Article, state.article_id) do
      ref = Process.monitor(socket)
      members = Map.put(state.members, socket, {ref, share_id})
      count = map_size(members)
      Enum.each(Map.keys(state.members), &send(&1, {:room_presence, count}))

      {:reply, {:ok, Articles.shared(article), count}, %{state | members: members}}
    else
      _ -> {:reply, {:error, :invalid_link}, state}
    end
  end

  @impl GenServer
  def handle_info({:article_updated, _, article}, state) do
    if article.revision > state.revision do
      Enum.each(Map.keys(state.members), &send(&1, {:room_updated, article}))
      {:noreply, %{state | revision: article.revision}}
    else
      {:noreply, state}
    end
  end

  def handle_info({:share_revoked, share_id}, state) do
    {revoked, kept} = Enum.split_with(state.members, fn {_pid, {_ref, id}} -> id == share_id end)

    Enum.each(revoked, fn {pid, {ref, _}} ->
      Process.demonitor(ref, [:flush])
      send(pid, :room_revoked)
    end)

    members = Map.new(kept)
    count = map_size(members)
    Enum.each(Map.keys(members), &send(&1, {:room_presence, count}))
    next_state(state, members)
  end

  def handle_info({:DOWN, ref, :process, pid, _}, state) do
    case Map.get(state.members, pid) do
      {^ref, _} ->
        members = Map.delete(state.members, pid)
        count = map_size(members)
        Enum.each(Map.keys(members), &send(&1, {:room_presence, count}))
        next_state(state, members)

      _ ->
        {:noreply, state}
    end
  end

  defp next_state(state, members) do
    if map_size(members) == 0,
      do: {:stop, :normal, %{state | members: members}},
      else: {:noreply, %{state | members: members}}
  end
end

defmodule Conduit.Rooms do
  use GenServer
  alias Conduit.Content

  def start_link(_), do: GenServer.start_link(__MODULE__, %{}, name: __MODULE__)
  def init(state), do: {:ok, state}
  def join(id, key, pid), do: GenServer.call(__MODULE__, {:join, id, key, pid})
  def leave(article_id, pid), do: GenServer.cast(__MODULE__, {:leave, article_id, pid})
  def updated(article), do: GenServer.cast(__MODULE__, {:updated, article})
  def revoked(article_id), do: GenServer.cast(__MODULE__, {:revoked, article_id})

  def handle_call({:join, id, key, pid}, _from, rooms) do
    case Content.shared_article(id, key) do
      {:ok, article} ->
        members = Map.get(rooms, article.id, %{})

        if map_size(members) >= 100 do
          {:reply, :full, rooms}
        else
          ref = Process.monitor(pid)
          members = Map.put(members, pid, ref)
          notify(Map.keys(members) -- [pid], {:presence, map_size(members)})
          {:reply, {:ok, article, map_size(members)}, Map.put(rooms, article.id, members)}
        end

      _ ->
        {:reply, :invalid, rooms}
    end
  end

  def handle_cast({:leave, id, pid}, rooms), do: {:noreply, remove(rooms, id, pid)}

  def handle_cast({:updated, article}, rooms) do
    notify(Map.keys(Map.get(rooms, article.id, %{})), {:updated, Content.shared(article)})
    {:noreply, rooms}
  end

  def handle_cast({:revoked, id}, rooms) do
    notify(Map.keys(Map.get(rooms, id, %{})), :revoked)
    {:noreply, Map.delete(rooms, id)}
  end

  def handle_info({:DOWN, _, :process, pid, _}, rooms) do
    id = Enum.find_value(rooms, fn {id, members} -> if Map.has_key?(members, pid), do: id end)
    {:noreply, if(id, do: remove(rooms, id, pid), else: rooms)}
  end

  defp remove(rooms, id, pid) do
    members = Map.get(rooms, id, %{})
    if ref = members[pid], do: Process.demonitor(ref, [:flush])
    members = Map.delete(members, pid)
    if ref, do: notify(Map.keys(members), {:presence, map_size(members)})
    Map.put(rooms, id, members)
  end

  defp notify(pids, message), do: Enum.each(pids, &send(&1, message))
end

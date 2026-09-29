defmodule ConduitWeb.ProfileController do
  use ConduitWeb, :controller
  alias ConduitWeb.API
  alias Conduit.Accounts

  def show(conn, %{"username" => name}) do
    case Accounts.find_profile(name) do
      {:error, reason} -> API.error(conn, reason)
      user -> API.reply(conn, 200, %{profile: Accounts.profile(user, API.caller(conn))})
    end
  end

  def follow(conn, %{"username" => name}), do: change_follow(conn, name, true)
  def unfollow(conn, %{"username" => name}), do: change_follow(conn, name, false)

  defp change_follow(conn, name, following?) do
    with {:ok, viewer} <- API.user(conn),
         target when not is_tuple(target) <- Accounts.find_profile(name) do
      API.reply(conn, 200, %{profile: Accounts.follow(viewer, target, following?)})
    else
      {:error, reason} -> API.error(conn, reason)
    end
  end
end

defmodule ConduitWeb.ProfileController do
  use ConduitWeb, :controller
  alias Conduit.Accounts
  alias ConduitWeb.Presenter

  action_fallback ConduitWeb.FallbackController

  def show(conn, %{"username" => username}) do
    with {:ok, profile} <- Accounts.fetch_profile(username) do
      json(conn, %{profile: Presenter.profile(profile, conn.assigns.current_user)})
    end
  end

  def follow(conn, %{"username" => username}) do
    with {:ok, profile} <- Accounts.fetch_profile(username) do
      Accounts.follow(conn.assigns.current_user, profile)
      json(conn, %{profile: Presenter.profile(profile, conn.assigns.current_user)})
    end
  end

  def unfollow(conn, %{"username" => username}) do
    with {:ok, profile} <- Accounts.fetch_profile(username) do
      Accounts.unfollow(conn.assigns.current_user, profile)
      json(conn, %{profile: Presenter.profile(profile, conn.assigns.current_user)})
    end
  end
end

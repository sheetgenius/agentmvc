defmodule ConduitWeb.UserController do
  use ConduitWeb, :controller
  alias Conduit.Accounts
  alias ConduitWeb.Presenter

  action_fallback ConduitWeb.FallbackController

  def create(conn, %{"user" => attrs}) do
    with {:ok, user} <- Accounts.register(attrs) do
      conn |> put_status(:created) |> json(%{user: Presenter.user(user)})
    end
  end

  def login(conn, %{"user" => %{"email" => email, "password" => password}})
      when is_binary(email) and byte_size(email) > 0 and is_binary(password) and
             byte_size(password) > 0 do
    with {:ok, user} <- Accounts.authenticate(email, password) do
      json(conn, %{user: Presenter.user(user)})
    end
  end

  def login(_conn, %{"user" => attrs}) do
    field = if is_binary(attrs["email"]) and attrs["email"] != "", do: :password, else: :email
    {:blank, field}
  end

  def show(conn, _params), do: json(conn, %{user: Presenter.user(conn.assigns.current_user)})

  def update(conn, %{"user" => attrs}) do
    with {:ok, user} <- Accounts.update(conn.assigns.current_user, attrs) do
      json(conn, %{user: Presenter.user(user)})
    end
  end
end

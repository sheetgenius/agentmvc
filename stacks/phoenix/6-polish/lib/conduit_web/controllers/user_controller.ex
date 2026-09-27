defmodule ConduitWeb.UserController do
  use ConduitWeb, :controller
  alias Conduit.Accounts
  alias ConduitWeb.Presenter

  action_fallback ConduitWeb.FallbackController

  def create(conn, %{"user" => %{} = attrs}) do
    with {:ok, user} <- Accounts.register(attrs) do
      conn |> put_status(:created) |> json(%{user: Presenter.user(user)})
    end
  end

  def create(_conn, _params), do: {:invalid, :user}

  def login(conn, %{"user" => %{"email" => email, "password" => password}})
      when is_binary(email) and byte_size(email) > 0 and is_binary(password) and
             byte_size(password) > 0 do
    with :ok <- throttle(email),
         {:ok, user} <- Accounts.authenticate(email, password) do
      json(conn, %{user: Presenter.user(user)})
    end
  end

  def login(_conn, %{"user" => %{} = attrs}) do
    field = if is_binary(attrs["email"]) and attrs["email"] != "", do: :password, else: :email
    {:blank, field}
  end

  def login(_conn, _params), do: {:invalid, :user}

  def show(conn, _params), do: json(conn, %{user: Presenter.user(conn.assigns.current_user)})

  def update(conn, %{"user" => %{} = attrs}) do
    with {:ok, user} <- Accounts.update(conn.assigns.current_user, attrs) do
      json(conn, %{user: Presenter.user(user)})
    end
  end

  def update(_conn, _params), do: {:invalid, :user}

  defp throttle(email) do
    key = :crypto.hash(:sha256, String.downcase(email))

    case ConduitWeb.LoginLimiter.hit(key, :timer.minutes(1), 10) do
      {:allow, _count} -> :ok
      {:deny, retry_after} -> {:rate_limited, retry_after}
    end
  end
end

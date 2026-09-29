defmodule ConduitWeb.UserController do
  use ConduitWeb, :controller
  alias ConduitWeb.API
  alias Conduit.Accounts
  alias Conduit.Articles
  alias Conduit.Exports

  def register(conn, params) do
    with {:ok, attrs} <- API.object(params, "user"),
         {:ok, user} <- Accounts.register(attrs) do
      API.reply(conn, 201, %{user: user_json(user)})
    else
      {:error, reason} -> API.error(conn, reason)
    end
  end

  def login(conn, params) do
    with {:ok, attrs} <- API.object(params, "user"),
         {:ok, user} <- Accounts.login(attrs) do
      API.reply(conn, 200, %{user: user_json(user)})
    else
      {:error, reason} -> API.error(conn, reason)
    end
  end

  def show(conn, _) do
    with {:ok, user} <- API.user(conn) do
      API.reply(conn, 200, %{user: user_json(user)})
    else
      {:error, reason} -> API.error(conn, reason)
    end
  end

  def update(conn, params) do
    with {:ok, user} <- API.user(conn),
         {:ok, attrs} <- API.object(params, "user"),
         {:ok, saved} <- Accounts.update(user, attrs) do
      API.reply(conn, 200, %{user: user_json(saved)})
    else
      {:error, reason} -> API.error(conn, reason)
    end
  end

  def drafts(conn, params) do
    with {:ok, user} <- API.user(conn) do
      {articles, count} = Articles.list(:drafts, {:user, user}, params)
      API.reply(conn, 200, %{articles: articles, articlesCount: count})
    else
      {:error, reason} -> API.error(conn, reason)
    end
  end

  def create_export(conn, _) do
    with {:ok, user} <- API.user(conn),
         {:ok, export} <- Exports.start(user) do
      API.reply(conn, 202, %{export: Exports.render(export)})
    else
      {:error, reason} -> API.error(conn, reason)
    end
  end

  def show_export(conn, %{"id" => id}) do
    with {:ok, user} <- API.user(conn),
         {:ok, export} <- Exports.get(user, id) do
      API.reply(conn, 200, %{export: Exports.render(export)})
    else
      {:error, reason} -> API.error(conn, reason)
    end
  end

  defp user_json(user) do
    %{
      email: user.email,
      username: user.username,
      bio: user.bio,
      image: user.image,
      token: Accounts.token(user)
    }
  end
end

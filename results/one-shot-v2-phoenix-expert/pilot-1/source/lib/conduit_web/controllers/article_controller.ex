defmodule ConduitWeb.ArticleController do
  use ConduitWeb, :controller
  alias ConduitWeb.API
  alias Conduit.Articles

  def index(conn, params) do
    {articles, count} = Articles.list(:global, API.caller(conn), params)
    API.reply(conn, 200, %{articles: articles, articlesCount: count})
  end

  def feed(conn, params) do
    with {:ok, user} <- API.user(conn) do
      {articles, count} = Articles.list(:feed, {:user, user}, params)
      API.reply(conn, 200, %{articles: articles, articlesCount: count})
    else
      {:error, reason} -> API.error(conn, reason)
    end
  end

  def tags(conn, _), do: API.reply(conn, 200, %{tags: Articles.tags()})

  def show(conn, %{"slug" => slug}) do
    with {:ok, article} <- Articles.get_visible(slug, API.caller(conn)) do
      API.reply(conn, 200, %{article: Articles.present_one(article, API.caller(conn))})
    else
      {:error, reason} -> API.error(conn, reason)
    end
  end

  def create(conn, params) do
    with {:ok, user} <- API.user(conn),
         {:ok, attrs} <- API.object(params, "article"),
         {:ok, article} <- Articles.create(user, attrs) do
      API.reply(conn, 201, %{article: Articles.present_one(article, {:user, user})})
    else
      {:error, reason} -> API.error(conn, reason)
    end
  end

  def update(conn, %{"slug" => slug} = params) do
    with {:ok, user} <- API.user(conn),
         {:ok, attrs} <- API.object(params, "article"),
         {:ok, article} <- Articles.commit({:author, user, slug}, attrs) do
      API.reply(conn, 200, %{article: Articles.present_one(article, {:user, user})})
    else
      {:error, reason} -> API.error(conn, reason)
    end
  end

  def delete(conn, %{"slug" => slug}) do
    with {:ok, user} <- API.user(conn),
         {:ok, _} <- Articles.delete(user, slug) do
      API.no_content(conn)
    else
      {:error, reason} -> API.error(conn, reason)
    end
  end

  def publish(conn, %{"slug" => slug}) do
    with {:ok, user} <- API.user(conn),
         {:ok, article} <- Articles.publish(user, slug) do
      API.reply(conn, 200, %{article: Articles.present_one(article, {:user, user})})
    else
      {:error, reason} -> API.error(conn, reason)
    end
  end

  def favorite(conn, %{"slug" => slug}), do: change_favorite(conn, slug, true)
  def unfavorite(conn, %{"slug" => slug}), do: change_favorite(conn, slug, false)

  defp change_favorite(conn, slug, active?) do
    with {:ok, user} <- API.user(conn),
         {:ok, article} <- Articles.get_visible(slug, {:user, user}),
         {:ok, saved} <- Articles.favorite(user, article, active?) do
      API.reply(conn, 200, %{article: Articles.present_one(saved, {:user, user})})
    else
      {:error, reason} -> API.error(conn, reason)
    end
  end
end

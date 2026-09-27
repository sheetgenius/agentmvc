defmodule ConduitWeb.ArticleController do
  use ConduitWeb, :controller
  alias Conduit.Content
  alias ConduitWeb.Presenter

  action_fallback ConduitWeb.FallbackController

  def index(conn, params) do
    render_list(conn, Content.list_articles(params, conn.assigns.current_user))
  end

  def feed(conn, params) do
    render_list(conn, Content.feed(conn.assigns.current_user, params))
  end

  def drafts(conn, params) do
    render_list(conn, Content.drafts(conn.assigns.current_user, params))
  end

  def show(conn, %{"slug" => slug}) do
    with {:ok, article} <- Content.fetch_article(slug, conn.assigns.current_user) do
      json(conn, %{article: Presenter.article(article, conn.assigns.current_user)})
    end
  end

  def create(conn, %{"article" => %{} = attrs}) do
    with {:ok, article} <- Content.create_article(conn.assigns.current_user, attrs) do
      conn
      |> put_status(:created)
      |> json(%{article: Presenter.article(article, conn.assigns.current_user)})
    end
  end

  def create(_conn, _params), do: {:invalid, :article}

  def update(conn, %{"slug" => slug, "article" => %{} = attrs}) do
    with {:ok, article} <- Content.fetch_article(slug, conn.assigns.current_user),
         {:ok, article} <- Content.update_article(article, conn.assigns.current_user, attrs) do
      json(conn, %{article: Presenter.article(article, conn.assigns.current_user)})
    else
      {:stale, article} ->
        conn
        |> put_status(:conflict)
        |> json(%{
          errors: %{revision: ["is stale"]},
          article: Presenter.article(article, conn.assigns.current_user)
        })

      error ->
        error
    end
  end

  def update(_conn, _params), do: {:invalid, :article}

  def delete(conn, %{"slug" => slug}) do
    with {:ok, article} <- Content.fetch_article(slug, conn.assigns.current_user),
         {:ok, _} <- Content.delete_article(article, conn.assigns.current_user) do
      send_resp(conn, :no_content, "")
    end
  end

  def publish(conn, %{"slug" => slug}) do
    with {:ok, article} <- Content.fetch_article(slug, conn.assigns.current_user),
         {:ok, article} <- Content.publish_article(article, conn.assigns.current_user) do
      json(conn, %{article: Presenter.article(article, conn.assigns.current_user)})
    end
  end

  def favorite(conn, %{"slug" => slug}) do
    with {:ok, article} <- Content.fetch_article(slug, conn.assigns.current_user),
         :ok <- Content.favorite(conn.assigns.current_user, article) do
      json(conn, %{article: Presenter.article(article, conn.assigns.current_user)})
    end
  end

  def unfavorite(conn, %{"slug" => slug}) do
    with {:ok, article} <- Content.fetch_article(slug, conn.assigns.current_user),
         :ok <- Content.unfavorite(conn.assigns.current_user, article) do
      json(conn, %{article: Presenter.article(article, conn.assigns.current_user)})
    end
  end

  def tags(conn, _params), do: json(conn, %{tags: Content.tags()})

  defp render_list(conn, {articles, count}) do
    json(conn, %{
      articles: Enum.map(articles, &Presenter.article(&1, conn.assigns.current_user, false)),
      articlesCount: count
    })
  end
end

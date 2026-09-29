defmodule ConduitWeb.Router do
  use ConduitWeb, :router

  pipeline :api do
    plug :accepts, ["json"]
    plug ConduitWeb.Plugs.Caller
    plug :put_secure_headers
  end

  defp put_secure_headers(conn, _opts),
    do: Plug.Conn.put_resp_header(conn, "x-content-type-options", "nosniff")

  scope "/", ConduitWeb do
    pipe_through :api
    get "/health", HealthController, :show
  end

  scope "/api", ConduitWeb do
    pipe_through :api
    post "/users", UserController, :register
    post "/users/login", UserController, :login
    get "/user", UserController, :show
    put "/user", UserController, :update
    get "/user/drafts", UserController, :drafts
    post "/user/exports", UserController, :create_export
    get "/user/exports/:id", UserController, :show_export
    get "/profiles/:username", ProfileController, :show
    post "/profiles/:username/follow", ProfileController, :follow
    delete "/profiles/:username/follow", ProfileController, :unfollow
    get "/tags", ArticleController, :tags
    get "/articles", ArticleController, :index
    get "/articles/feed", ArticleController, :feed
    post "/articles", ArticleController, :create
    get "/articles/:slug", ArticleController, :show
    put "/articles/:slug", ArticleController, :update
    delete "/articles/:slug", ArticleController, :delete
    post "/articles/:slug/publish", ArticleController, :publish
    post "/articles/:slug/favorite", ArticleController, :favorite
    delete "/articles/:slug/favorite", ArticleController, :unfavorite
    get "/articles/:slug/comments", CommentController, :index
    post "/articles/:slug/comments", CommentController, :create
    delete "/articles/:slug/comments/:id", CommentController, :delete
    post "/articles/:slug/share", ShareController, :create
    delete "/articles/:slug/share", ShareController, :delete
    get "/shares/:id/article", ShareController, :show_article
    put "/shares/:id/article", ShareController, :update_article
    get "/shares/:id/live", ShareController, :live
  end
end

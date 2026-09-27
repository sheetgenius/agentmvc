defmodule ConduitWeb.Router do
  use ConduitWeb, :router

  pipeline :api do
    plug :accepts, ["json"]
    plug :put_secure_browser_headers
    plug ConduitWeb.Auth, :fetch_user
  end

  pipeline :authenticated do
    plug ConduitWeb.Auth, :require_user
  end

  scope "/api", ConduitWeb do
    pipe_through [:api, :authenticated]

    get "/user", UserController, :show
    put "/user", UserController, :update
    get "/user/drafts", ArticleController, :drafts
    post "/user/exports", ExportController, :create
    get "/user/exports/:id", ExportController, :show
    post "/profiles/:username/follow", ProfileController, :follow
    delete "/profiles/:username/follow", ProfileController, :unfollow
    get "/articles/feed", ArticleController, :feed
    post "/articles", ArticleController, :create
    put "/articles/:slug", ArticleController, :update
    delete "/articles/:slug", ArticleController, :delete
    post "/articles/:slug/publish", ArticleController, :publish
    post "/articles/:slug/share", ShareController, :create
    delete "/articles/:slug/share", ShareController, :delete
    post "/articles/:slug/favorite", ArticleController, :favorite
    delete "/articles/:slug/favorite", ArticleController, :unfavorite
    post "/articles/:slug/comments", CommentController, :create
    delete "/articles/:slug/comments/:id", CommentController, :delete
  end

  scope "/api", ConduitWeb do
    pipe_through :api

    post "/users", UserController, :create
    post "/users/login", UserController, :login
    get "/profiles/:username", ProfileController, :show
    get "/articles", ArticleController, :index
    get "/articles/:slug", ArticleController, :show
    get "/articles/:slug/comments", CommentController, :index
    get "/shares/:id/article", ShareController, :show_article
    put "/shares/:id/article", ShareController, :update_article
    get "/tags", ArticleController, :tags
  end
end

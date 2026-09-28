defmodule ConduitWeb.Router do
  use ConduitWeb, :router

  pipeline :api do
    plug :accepts, ["json"]
    plug ConduitWeb.ApiHeaders
  end

  scope "/api", ConduitWeb do
    pipe_through :api
    post "/users", ApiController, :register
    post "/users/login", ApiController, :login
    get "/user", ApiController, :current
    put "/user", ApiController, :update_user
    get "/user/drafts", ApiController, :drafts
    post "/user/exports", ApiController, :export_create
    get "/user/exports/:id", ApiController, :export_show
    get "/profiles/:username", ApiController, :profile
    post "/profiles/:username/follow", ApiController, :follow
    delete "/profiles/:username/follow", ApiController, :unfollow
    get "/tags", ApiController, :tags
    get "/articles/feed", ApiController, :feed
    get "/articles", ApiController, :articles
    post "/articles", ApiController, :article_create
    get "/articles/:slug", ApiController, :article_show
    put "/articles/:slug", ApiController, :article_update
    delete "/articles/:slug", ApiController, :article_delete
    post "/articles/:slug/publish", ApiController, :publish
    get "/articles/:slug/comments", ApiController, :comments
    post "/articles/:slug/comments", ApiController, :comment_create
    delete "/articles/:slug/comments/:id", ApiController, :comment_delete
    post "/articles/:slug/favorite", ApiController, :favorite
    delete "/articles/:slug/favorite", ApiController, :unfavorite
    post "/articles/:slug/share", ApiController, :share_create
    delete "/articles/:slug/share", ApiController, :share_delete
    get "/shares/:id/article", ApiController, :shared_show
    put "/shares/:id/article", ApiController, :shared_update
    get "/shares/:id/live", ApiController, :live
    options "/*path", ApiController, :options
    match :*, "/*path", ApiController, :unknown
  end
end

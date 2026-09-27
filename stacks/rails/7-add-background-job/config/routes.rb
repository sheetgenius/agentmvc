Rails.application.routes.draw do
  namespace :api do
    post "users/login", to: "sessions#create"
    resources :users, only: :create
    resource :user, only: [ :show, :update ]
    resources :exports, only: [ :create, :show ], path: "user/exports"
    get "user/drafts", to: "articles#drafts"
    resources :profiles, only: :show, param: :username do
      post :follow, on: :member
      delete :follow, on: :member, action: :unfollow
    end
    resources :articles, only: [ :index, :show, :create, :update, :destroy ], param: :slug do
      get :feed, on: :collection
      post :publish, on: :member
      post :favorite, on: :member
      delete :favorite, on: :member, action: :unfavorite
      resources :comments, only: [ :index, :create, :destroy ]
    end
    resources :tags, only: :index
  end
end

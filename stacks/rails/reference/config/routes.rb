Rails.application.routes.draw do
  namespace :api do
    post "users/login", to: "users#login"
    resources :users, only: :create
    resource :user, only: %i[show update], controller: :user
    get "user/drafts", to: "articles#drafts"
    post "user/exports", to: "exports#create"
    get "user/exports/:id", to: "exports#show"
    resources :profiles, only: :show, param: :username do
      post :follow, on: :member
      delete :follow, on: :member, action: :unfollow
    end
    resources :articles, only: %i[index show create update destroy], param: :slug do
      get :feed, on: :collection
      resources :comments, only: %i[index create destroy]
      post :favorite, on: :member
      delete :favorite, on: :member, action: :unfavorite
      post :publish, on: :member
      post :share, on: :member
      delete :share, on: :member, action: :unshare
    end
    get "tags", to: "tags#index"
    get "shares/:id/article", to: "shares#show"
    put "shares/:id/article", to: "shares#update"
    get "shares/:id/live", to: "shares#live"
  end
  match "api/*unmatched", to: "api/errors#not_found", via: :all
  # Define your application routes per the DSL in https://guides.rubyonrails.org/routing.html

  # Reveal health status on /up that returns 200 if the app boots with no exceptions, otherwise 500.
  # Can be used by load balancers and uptime monitors to verify that the app is live.
  get "up" => "rails/health#show", as: :rails_health_check

  # Defines the root path route ("/")
  # root "posts#index"
end

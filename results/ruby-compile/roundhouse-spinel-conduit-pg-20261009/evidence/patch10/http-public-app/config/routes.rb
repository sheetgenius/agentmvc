Rails.application.routes.draw do
  get "/widgets", to: "widgets#show"
  get "/requests", to: "requests#show"
  get "/problems", to: "problems#show"
  get "/forms", to: "forms#show"
  get "/failures", to: "failures#show"
  get "/empty", to: "empty#show"
  get "/cached", to: "empty#cached"
  get "/callbacks", to: "callbacks#show"
  get "/numeric", to: "status#show"
  get "/parse", to: "failures#parse"
end

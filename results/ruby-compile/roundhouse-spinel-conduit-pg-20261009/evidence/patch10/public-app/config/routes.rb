Rails.application.routes.draw do
  get "/widgets", to: "widgets#show"
  get "/requests", to: "requests#show"
  get "/problems", to: "problems#show"
  get "/forms", to: "forms#show"
  get "/failures", to: "failures#show"
  get "/empty", to: "empty#show"
end

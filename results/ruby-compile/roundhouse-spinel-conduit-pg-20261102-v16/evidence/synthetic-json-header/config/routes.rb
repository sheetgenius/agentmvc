Rails.application.routes.draw do
  get "/probe", to: "probes#show"
end

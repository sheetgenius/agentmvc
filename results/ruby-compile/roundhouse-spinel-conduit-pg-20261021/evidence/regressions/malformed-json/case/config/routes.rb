Rails.application.routes.draw do
  post "/probe", to: "probe#create"
end

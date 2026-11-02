require "rails/all"

module SyntheticTransport
  class Application < Rails::Application
    config.api_only = true
  end
end

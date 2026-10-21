require "bundler/setup"
require "rails"
require "action_controller/railtie"
require "rack/mock"
class Mini < Rails::Application
  config.root = "/probe/case"
  config.api_only = true
  config.eager_load = false
  config.secret_key_base = "0123456789abcdef" * 8
  config.hosts.clear
  config.logger = Logger.new(nil)
end
require "/probe/case/app/controllers/probe_controller"
Mini.initialize!
r = Rack::MockRequest.new(Mini).post("/probe", "CONTENT_TYPE" => "application/json", input: "{")
p [r.status, r.body]

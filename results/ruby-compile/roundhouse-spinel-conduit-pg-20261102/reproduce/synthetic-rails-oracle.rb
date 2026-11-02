require 'rails'
require 'action_controller/railtie'
require 'json'
require 'rack/mock'
require 'tmpdir'

module HeaderOracle
  class Application < Rails::Application
    config.root = Dir.mktmpdir('conduit-v15-json-oracle-')
    config.load_defaults ENV.fetch('ORACLE_DEFAULTS', '8.1').to_f
    config.api_only = true
    config.eager_load = false
    config.secret_key_base = '0123456789abcdef' * 8
    config.hosts.clear
    config.logger = Logger.new(File::NULL)
  end
end
class ApplicationController < ActionController::API
end
class ProbesController < ApplicationController
  def show
    render json: { ok: true }
  end
end
app=HeaderOracle::Application.initialize!
app.routes.draw { get '/probe', to: 'probes#show' }
response=Rack::MockRequest.new(app).get('/probe', 'HTTP_ACCEPT'=>'application/json')
puts JSON.generate(ruby: RUBY_VERSION, rails: Rails.version, defaults: ENV.fetch('ORACLE_DEFAULTS','8.1'),
  api_only: app.config.api_only, status: response.status, content_type: response['content-type'],
  body: JSON.parse(response.body))

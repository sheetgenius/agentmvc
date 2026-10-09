class ApplicationController < ActionController::API
  rescue_from ActionController::ParameterMissing do |failure|
    render json: { error: failure.message }, status: 422
  end
  after_action { response.set_header("X-Mode", "api") }
end

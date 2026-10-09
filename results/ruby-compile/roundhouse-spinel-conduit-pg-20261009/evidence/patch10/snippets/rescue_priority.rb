class ApplicationController < ActionController::API
  rescue_from ActionController::ParameterMissing do |failure|
    render json: { error: failure.message }, status: 422
  end
end
class WidgetsController < ApplicationController
  rescue_from ActionController::ParameterMissing do |failure|
    render json: { error: failure.message }, status: 409
  end
  def show
    params.require(:widget)
  end
end

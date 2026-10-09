class WidgetsController < ApplicationController
  rescue_from ActionController::ParameterMissing do |failure|
    render json: { error: failure.message }, status: 409
  end
  def show
    params.require(:widget)
    render json: { name: "ready" }, status: 202
  end
end

class FailuresController < ApplicationController
  rescue_from ActionController::BadRequest, ActionDispatch::Http::Parameters::ParseError do |failure|
    render json: { error: failure.message }, status: 400
  end
  def show
    raise ActionController::BadRequest, "invalid input"
  end
end

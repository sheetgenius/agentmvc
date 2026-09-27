class ApplicationController < ActionController::API
  helper_method :current_user

  rescue_from ActiveRecord::RecordNotFound do |error|
    resource = error.model == "User" ? :profile : error.model.underscore
    render_error(resource, "not found", :not_found)
  end
  rescue_from ActiveRecord::RecordInvalid do |error|
    render_validation(error.record)
  end

  private

  def current_user
    return @current_user if defined?(@current_user)

    token = request.authorization&.match(/\AToken (.+)\z/)&.captures&.first
    payload = JWT.decode(token, Rails.application.secret_key_base, true, algorithm: "HS256").first if token
    @current_user = User.find_by(id: payload["sub"]) if payload
  rescue JWT::DecodeError
    @current_user = nil
  end

  def authenticate_user!
    render_error(:token, "is missing", :unauthorized) unless current_user
  end

  def reject_draft
    render_error(:article, "is a draft", :unprocessable_content) if @article.draft?
  end

  def render_error(field, message, status)
    render json: { errors: { field => [ message ] } }, status: status
  end

  def render_validation(record)
    conflict = record.errors.details.values.flatten.any? { |error| error[:error] == :taken }
    render json: { errors: record.errors.to_hash }, status: conflict ? :conflict : :unprocessable_content
  end
end

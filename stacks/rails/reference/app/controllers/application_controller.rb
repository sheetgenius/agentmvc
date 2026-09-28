class ApplicationController < ActionController::API
  before_action :load_viewer
  rescue_from ActiveRecord::RecordInvalid do |error|
    status = error.record.errors.attribute_names.any? { |name| error.record.errors.of_kind?(name, :taken) } ? :conflict : :unprocessable_entity
    render json: { errors: error.record.errors.to_hash }, status: status
  end
  rescue_from ActiveRecord::RecordNotFound, with: :not_found
  rescue_from ActionController::ParameterMissing, ActionController::BadRequest, JSON::ParserError do
    render_error(:body, "is invalid", :unprocessable_entity)
  end

  private

  attr_reader :current_user

  def load_viewer
    credential = request.authorization.to_s[/\AToken (.+)\z/, 1]
    @current_user = Token.read(credential) if credential
  end

  def authenticate_user!
    render_error(:token, request.authorization.present? ? "is invalid" : "is missing", :unauthorized) unless current_user
  end

  def presenter
    @presenter ||= ConduitJson.new(current_user)
  end

  def render_error(field, message, status)
    render json: { errors: { field => [ message ] } }, status: status
  end

  def not_found
    render_error(:article, "not found", :not_found)
  end

  def owner!(record, field = :article)
    return true if record.author_id == current_user.id
    render_error(field, "forbidden", :forbidden)
    false
  end

  def input(key)
    value = params.require(key)
    raise ActionController::BadRequest unless value.is_a?(ActionController::Parameters)
    value
  end

  def page(relation)
    count = relation.count
    limit = Integer(params.fetch(:limit, 20), exception: false)&.clamp(0, 100) || 20
    offset = Integer(params.fetch(:offset, 0), exception: false)&.clamp(0, 1_000_000) || 0
    { articles: relation.order(created_at: :desc, id: :desc).limit(limit).offset(offset).map { |article| presenter.article(article, body: false) },
      articlesCount: count }
  end
end

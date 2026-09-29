class ApplicationController < ActionController::API
  class Failure < StandardError
    attr_reader :status, :errors, :extra
    def initialize(status, field, message, extra = {})
      @status, @errors, @extra = status, { field => [ message ] }, extra
    end
  end

  rescue_from Failure do |failure|
    render json: { errors: failure.errors }.merge(failure.extra), status: failure.status
  end
  rescue_from ActiveRecord::RecordInvalid do |failure|
    render json: { errors: failure.record.errors.to_hash }, status: :unprocessable_entity
  end
  rescue_from ActiveRecord::RecordNotUnique do
    render json: { errors: { base: [ "has already been taken" ] } }, status: :conflict
  end
  rescue_from ActionDispatch::Http::Parameters::ParseError, ActionController::BadRequest do
    render json: { errors: { body: [ "is invalid" ] } }, status: :bad_request
  end

  def not_found
    render json: { errors: { route: [ "not found" ] } }, status: :not_found
  end

  before_action :read_user
  after_action { response.set_header("X-Content-Type-Options", "nosniff") }

  def read_user
    header = request.authorization.to_s
    return if header.empty?
    raise Failure.new(401, :token, "is invalid") unless header.start_with?("Token ")
    payload = JWT.decode(header.delete_prefix("Token "), Rails.application.secret_key_base, true, algorithm: "HS256").first
    @current_user = User.find_by(id: payload["sub"])
    raise Failure.new(401, :token, "is invalid") unless @current_user
  rescue JWT::DecodeError
    raise Failure.new(401, :token, "is invalid")
  end

  def require_user!
    raise Failure.new(401, :token, "is missing") unless @current_user
  end

  def object!(name)
    value = params[name]
    raise Failure.new(422, name, "is invalid") unless value.is_a?(ActionController::Parameters)
    value
  end

  def article!
    article = Article.find_by(slug: params[:slug])
    raise Failure.new(404, :article, "not found") unless article && (article.status == "published" || article.author_id == @current_user&.id)
    article
  end

  def author_article!
    require_user!
    article = article!
    raise Failure.new(403, :article, "forbidden") unless article.author_id == @current_user.id
    article
  end

  def public_article!
    article = article!
    raise Failure.new(422, :article, "is a draft") if article.status == "draft"
    article
  end

  def profile_json(user, following_ids = nil)
    following = if @current_user
      following_ids ? following_ids.include?(user.id) : Follow.exists?(follower_id: @current_user.id, followed_id: user.id)
    else
      false
    end
    { username: user.username, bio: user.bio, image: user.image, following: following }
  end

  def article_json(article, list: false, following_ids: nil, favorite_ids: nil, favorite_counts: nil)
    author = article.association(:author).loaded? ? article.author : article.author
    favorited = @current_user && (favorite_ids ? favorite_ids.include?(article.id) : Favorite.exists?(user_id: @current_user.id, article_id: article.id))
    count = favorite_counts ? favorite_counts.fetch(article.id, 0) : Favorite.where(article_id: article.id).count
    data = { slug: article.slug, title: article.title, description: article.description,
      tagList: article.tag_list, createdAt: article.created_at.iso8601(3), updatedAt: article.updated_at.iso8601(3),
      favorited: !!favorited, favoritesCount: count, author: profile_json(author, following_ids),
      status: article.status, publishedAt: article.published_at&.iso8601(3), revision: article.revision }
    data[:body] = article.body unless list
    data
  end

  def article_page(relation)
    limit = Integer(params.fetch(:limit, 20)) rescue 20
    offset = Integer(params.fetch(:offset, 0)) rescue 0
    limit = limit.clamp(0, 100)
    offset = offset.clamp(0, 1_000_000)
    count = relation.count
    articles = relation.order(created_at: :desc, id: :desc).limit(limit).offset(offset).includes(:author).to_a
    ids = articles.map(&:id)
    author_ids = articles.map(&:author_id)
    following_ids = @current_user ? Follow.where(follower_id: @current_user.id, followed_id: author_ids).pluck(:followed_id).to_set : nil
    favorite_ids = @current_user ? Favorite.where(user_id: @current_user.id, article_id: ids).pluck(:article_id).to_set : nil
    favorite_counts = Favorite.where(article_id: ids).group(:article_id).count
    { articles: articles.map { |a| article_json(a, list: true, following_ids: following_ids, favorite_ids: favorite_ids, favorite_counts: favorite_counts) }, articlesCount: count }
  end
end

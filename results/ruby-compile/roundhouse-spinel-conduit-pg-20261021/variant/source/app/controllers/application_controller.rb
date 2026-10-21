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
  rescue_from JSON::ParserError, ActionDispatch::Http::Parameters::ParseError, ActionController::BadRequest do
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
    payload = TokenCodec.decode(header.delete_prefix("Token "), Rails.application.secret_key_base)
    @current_user = User.find_by(id: payload["sub"])
    raise Failure.new(401, :token, "is invalid") unless @current_user
  rescue TokenCodec::DecodeError
    raise Failure.new(401, :token, "is invalid")
  end

  def require_user!
    raise Failure.new(401, :token, "is missing") unless @current_user
  end

  # Compile variant: the compiled lane's `params` hold strings only, so JSON request bodies are
  # read here with their JSON types. Rails parses a JSON body lazily on the first `params` read
  # (malformed -> ParseError -> 400 below); `param` parses first to keep that error order.
  JSON_MEDIA_TYPES = %w[application/json text/x-json application/jsonrequest].freeze
  # ParamsWrapper (on by default for JSON in API mode) nests unwrapped bodies under the
  # controller's model name, keeping only the model's attribute names.
  WRAPPED_ATTRIBUTES = {
    "user" => %w[id username email password_digest bio image created_at updated_at],
    "article" => %w[id author_id slug title description body tag_list status published_at revision created_at updated_at],
    "comment" => %w[id article_id author_id body created_at updated_at]
  }.freeze

  def json_body
    unless @json_body_parsed
      media = request.headers["Content-Type"].to_s.split(";").first.to_s.strip.downcase
      raw = request.raw_post.to_s
      value = JSON_MEDIA_TYPES.include?(media) && !raw.empty? ? JSON.parse(raw) : {}
      @json_body = value.is_a?(Hash) ? value : {}
      @json_media = JSON_MEDIA_TYPES.include?(media)
      @json_body_parsed = true
    end
    @json_body
  end

  def param(name)
    json_body
    params[name]
  end

  # `wrap: false` where the controller's ParamsWrapper key differs from `name` (SharesController wraps as "share").
  def object!(name, wrap: true)
    body = json_body
    key = name.to_s
    value = body[key]
    attributes = WRAPPED_ATTRIBUTES[key]
    if wrap && @json_media && attributes && !body.key?(key)
      value = body.slice(*attributes)
    end
    raise Failure.new(422, name, "is invalid") unless value.is_a?(Hash)
    value
  end

  # Roundhouse drops controller rest parameters and expects symbol attribute keys.
  # Strong-parameter `permit` for scalars, then Active Model's string cast.
  def permitted(input, names)
    out = {}
    names.each do |name|
      key = name.to_s
      next unless input.key?(key)
      value = input[key]
      next if value.is_a?(Hash) || value.is_a?(Array)
      out[name] = string_cast(value)
    end
    out
  end

  def string_cast(value)
    JsonCast.string(value)
  end

  def article!
    article = Article.find_by(slug: param(:slug))
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
    # Roundhouse cannot dispatch belongs_to Association#loaded?; both reference branches read author.
    author = article.author
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
    limit = Integer(param(:limit) || 20) rescue 20
    offset = Integer(param(:offset) || 0) rescue 0
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

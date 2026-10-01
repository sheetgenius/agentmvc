class ArticlesController < ApplicationController
  def index
    relation = Article.published
    relation = relation.where("tag_list @> ARRAY[?]::text[]", param(:tag)) if param(:tag).present?
    relation = relation.joins(:author).where(users: { username: param(:author) }) if param(:author).present?
    relation = relation.where(id: Favorite.joins(:user).where(users: { username: param(:favorited) }).select(:article_id)) if param(:favorited).present?
    render json: article_page(relation)
  end

  def feed
    require_user!
    relation = Article.published.where(author_id: Follow.where(follower_id: @current_user.id).select(:followed_id))
    render json: article_page(relation)
  end

  def drafts
    require_user!
    render json: article_page(Article.where(author_id: @current_user.id, status: "draft"))
  end

  def show
    render json: { article: article_json(article!) }
  end

  def create
    require_user!
    input = object!(:article)
    status = input.fetch("status", "published")
    raise Failure.new(422, :status, "is invalid") unless %w[draft published].include?(status)
    # Spinel Hash#fetch with an Array default returns nil for an absent key.
    tags = input.key?("tagList") ? input["tagList"] : []
    raise Failure.new(422, :tagList, "is invalid") unless tags.is_a?(Array) && tags.all? { |tag| tag.is_a?(String) }
    article = Article.new(permitted(input, %i[title description body]).merge(
      author: @current_user, status: status, published_at: (Time.current if status == "published"),
      tag_list: tags.uniq, slug: Article.slug_for(input["title"])))
    article.save!
    render json: { article: article_json(article) }, status: :created
  end

  def update
    article = author_article!
    input = object!(:article)
    ArticleCommit.call(article, input, expected: input["revision"], representation: ->(a) { article_json(a) })
    render json: { article: article_json(article) }
  end

  def destroy
    article = author_article!
    LiveRooms.revoked(article.article_shares.active.pluck(:id))
    article.destroy!
    head :no_content
  end

  def publish
    article = author_article!
    article.publish!
    render json: { article: article_json(article) }
  end
end

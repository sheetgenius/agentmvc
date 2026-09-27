module Api
  class ArticlesController < ApplicationController
    before_action :authenticate_user!, only: [ :feed, :drafts, :create, :update, :destroy, :publish, :favorite, :unfavorite, :share, :revoke_share ]
    before_action :set_article, only: [ :show, :update, :destroy, :publish, :favorite, :unfavorite, :share, :revoke_share ]
    before_action :authorize_article, only: [ :update, :destroy, :publish, :share, :revoke_share ]
    before_action :reject_draft, only: [ :favorite, :unfavorite ]
    before_action :set_pagination, only: [ :index, :feed, :drafts ]

    def index
      articles = Article.published
      articles = articles.by_author(params[:author]) if params[:author].present?
      articles = articles.tagged(params[:tag]) if params[:tag].present?
      articles = articles.favorited_by(params[:favorited]) if params[:favorited].present?
      list(articles)
    end

    def feed
      list(Article.published.where(author: current_user.followed_users))
      render :index
    end

    def drafts
      list(current_user.articles.draft)
      render :index
    end

    def show; end

    def create
      return if invalid_tags?(params[:article])
      payload = params.expect(article: [ :title, :description, :body, :status, { tagList: [] } ])

      Article.transaction do
        @article = current_user.articles.create!(payload.permit(:title, :description, :body, :status))
        @article.replace_tags(payload[:tagList]) if payload[:tagList]
      end
      render :show, status: :created
    end

    def update
      return if invalid_tags?(params[:article])

      payload = params.expect(article: [ :title, :description, :body, :revision, { tagList: [] } ])
      revision = params[:article][:revision]
      return render_error(:revision, "is invalid", :unprocessable_content) if params[:article].key?(:revision) && !revision.is_a?(Integer)

      if @article.revise!(payload.permit(:title, :description, :body), expected_revision: revision, tag_list: payload[:tagList])
        render :show
      else
        render :conflict, status: :conflict
      end
    end

    def destroy
      @article.destroy!
      head :no_content
    end

    def publish
      @article.publish!
      render :show
    end

    def share
      @article.with_lock do
        @article.article_share&.destroy!
        @share, @key = ArticleShare.issue!(@article)
      end
      render json: { share: { id: @share.public_id, key: @key } }, status: :created
    end

    def revoke_share
      @article.with_lock { @article.article_share&.destroy! }
      head :no_content
    end

    def favorite
      current_user.favorites.find_or_create_by!(article: @article)
      render :show
    end

    def unfavorite
      current_user.favorites.where(article: @article).delete_all
      render :show
    end

    private

    def set_article
      @article = Article.visible_to(current_user).find_by!(slug: params[:slug])
    end

    def authorize_article
      render_error(:article, "forbidden", :forbidden) unless @article.author == current_user
    end

    def invalid_tags?(payload)
      return false unless payload.is_a?(ActionController::Parameters) && payload.key?(:tagList)
      return false if payload[:tagList].is_a?(Array) && payload[:tagList].all? { |name| name.is_a?(String) && name.present? }

      render_error(:tagList, "must be a list of nonempty strings", :unprocessable_content)
      true
    end

    def set_pagination
      @limit = Integer(params.fetch(:limit, 20), exception: false)
      @offset = Integer(params.fetch(:offset, 0), exception: false)
      return render_error(:limit, "is invalid", :unprocessable_content) unless @limit&.between?(0, 1000)

      render_error(:offset, "is invalid", :unprocessable_content) unless @offset&.between?(0, 1_000_000)
    end

    def list(articles)
      @articles_count = articles.count
      @articles = articles.recent.includes(:author, :tags, :favorites).limit(@limit).offset(@offset)
      current_user.followed_users.load if current_user
    end
  end
end

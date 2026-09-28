module Api
  class ArticlesController < ApplicationController
    before_action :authenticate_user!, only: %i[feed drafts create update destroy publish favorite unfavorite share unshare]
    before_action :find_article, only: %i[show update destroy publish favorite unfavorite share unshare]

    def index
      articles = Article.published
      articles = articles.authored_by(params[:author]) if params[:author]
      articles = articles.favorited_by(params[:favorited]) if params[:favorited]
      articles = articles.tagged_with(params[:tag]) if params[:tag]
      render json: page(articles)
    end

    def feed
      render json: page(Article.published.where(author: current_user.followed_users))
    end

    def drafts
      render json: page(current_user.articles.draft)
    end

    def show
      render_article
    end

    def create
      fields = article_fields
      article = current_user.articles.create!(fields)
      render json: { article: presenter.article(article) }, status: :created
    end

    def update
      return unless owner!(@article)
      @article.with_lock do
        fields = input(:article)
        return if revision_error(fields[:revision], fields.key?(:revision))
        @article.update!(article_fields)
      end
      LiveRooms.updated(@article)
      render_article
    end

    def destroy
      return unless owner!(@article)
      @article.destroy!
      head :no_content
    end

    def publish
      return unless owner!(@article)
      @article.update!(status: "published", published_at: Time.current) if @article.draft?
      render_article
    end

    def favorite
      return render_error(:article, "is a draft", :unprocessable_entity) if @article.draft?
      current_user.favorites.find_or_create_by!(article: @article)
      render_article
    end

    def unfavorite
      current_user.favorites.where(article: @article).delete_all
      render_article
    end

    def share
      return unless owner!(@article)
      share = @article.share || @article.build_share
      old_id = share.public_id
      key = share.rotate!
      LiveRooms.revoke(old_id) if old_id
      render json: { share: { id: share.public_id, key: key } }, status: :created
    end

    def unshare
      return unless owner!(@article)
      if (share = @article.share)
        share.destroy!
        LiveRooms.revoke(share.public_id)
      end
      head :no_content
    end

    private

    def find_article
      @article = Article.visible_to(current_user).find_by!(slug: params[:slug])
    end

    def article_fields
      fields = input(:article)
      attributes = fields.permit(:title, :description, :body).to_h
      attributes[:status] = fields[:status] if action_name == "create" && fields.key?(:status)
      if fields.key?(:tagList)
        return raise ActionController::BadRequest unless fields[:tagList].is_a?(Array)
        attributes[:tags] = fields[:tagList]
      end
      attributes
    end

    def revision_error(revision, supplied)
      return false unless supplied
      return render_error(:revision, "is invalid", :unprocessable_entity) || true unless revision.is_a?(Integer)
      return false if revision == @article.revision
      render json: { errors: { revision: [ "is stale" ] }, article: presenter.article(@article) }, status: :conflict
      true
    end

    def render_article
      render json: { article: presenter.article(@article) }
    end
  end
end

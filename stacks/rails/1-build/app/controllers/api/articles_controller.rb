module Api
  class ArticlesController < ApplicationController
    before_action :authenticate_user!, only: [ :feed, :create, :update, :destroy, :favorite, :unfavorite ]
    before_action :set_article, only: [ :show, :update, :destroy, :favorite, :unfavorite ]
    before_action :authorize_article, only: [ :update, :destroy ]

    def index
      articles = Article.all
      articles = articles.by_author(params[:author]) if params[:author].present?
      articles = articles.tagged(params[:tag]) if params[:tag].present?
      articles = articles.favorited_by(params[:favorited]) if params[:favorited].present?
      list(articles)
    end

    def feed
      list(Article.where(author: current_user.followed_users))
      render :index
    end

    def show; end

    def create
      payload = params.require(:article)
      return if invalid_tags?(payload)

      Article.transaction do
        @article = current_user.articles.create!(payload.permit(:title, :description, :body))
        assign_tags(payload) if payload.key?(:tagList)
      end
      render :show, status: :created
    end

    def update
      payload = params.require(:article)
      return if invalid_tags?(payload)

      Article.transaction do
        @article.update!(payload.permit(:title, :description, :body))
        assign_tags(payload) if payload.key?(:tagList)
      end
      render :show
    end

    def destroy
      @article.destroy!
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
      @article = Article.find_by!(slug: params[:slug])
    end

    def authorize_article
      render_error(:article, "forbidden", :forbidden) unless @article.author == current_user
    end

    def invalid_tags?(payload)
      return false unless payload.key?(:tagList)
      return false if payload[:tagList].is_a?(Array) && payload[:tagList].all? { |name| name.is_a?(String) && name.present? }

      render_error(:tagList, "must be a list of nonempty strings", :unprocessable_content)
      true
    end

    def assign_tags(payload)
      @article.tags = payload[:tagList].uniq.map { |name| Tag.find_or_create_by!(name: name) }
    end

    def list(articles)
      @articles_count = articles.count
      @articles = articles.recent.limit(params.fetch(:limit, 20).to_i).offset(params.fetch(:offset, 0).to_i)
    end
  end
end

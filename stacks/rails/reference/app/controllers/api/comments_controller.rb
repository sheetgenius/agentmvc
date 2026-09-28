module Api
  class CommentsController < ApplicationController
    before_action :authenticate_user!, only: %i[create destroy]
    before_action :find_article

    def index
      render json: { comments: @article.comments.order(:id).map { |comment| presenter.comment(comment) } }
    end

    def create
      return render_error(:article, "is a draft", :unprocessable_entity) if @article.draft?
      comment = @article.comments.create!(author: current_user, body: input(:comment)[:body])
      render json: { comment: presenter.comment(comment) }, status: :created
    end

    def destroy
      comment = @article.comments.find_by(id: params[:id].to_s[/\A\d+\z/])
      return render_error(:comment, "not found", :not_found) unless comment
      return unless owner!(comment, :comment)
      comment.destroy!
      head :no_content
    end

    private

    def find_article
      @article = Article.visible_to(current_user).find_by!(slug: params[:article_slug])
    end
  end
end

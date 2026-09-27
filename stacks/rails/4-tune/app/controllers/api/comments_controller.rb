module Api
  class CommentsController < ApplicationController
    before_action :authenticate_user!, only: [ :create, :destroy ]
    before_action :set_article
    before_action :reject_draft, only: :create

    def index
      @comments = @article.comments.includes(:author).order(:created_at, :id)
    end

    def create
      @comment = @article.comments.create!(params.require(:comment).permit(:body).merge(author: current_user))
      render :show, status: :created
    end

    def destroy
      comment = @article.comments.find(params[:id])
      return render_error(:comment, "forbidden", :forbidden) unless comment.author == current_user

      comment.destroy!
      head :no_content
    end

    private

    def set_article
      @article = Article.visible_to(current_user).find_by!(slug: params[:article_slug])
    end
  end
end

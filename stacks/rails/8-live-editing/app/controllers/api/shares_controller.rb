module Api
  class SharesController < ApplicationController
    before_action :authenticate_share

    def show
      render json: { article: @share.article.shared_payload }
    end

    def update
      payload = params[:article]
      return render_error(:article, "is invalid", :unprocessable_content) unless valid_edit?(payload)

      article = @share.article
      attributes = payload.permit(:title, :body, :revision).except(:revision)
      if article.revise!(attributes, expected_revision: payload[:revision])
        render json: { article: article.shared_payload }
      else
        render json: { errors: { revision: [ "is stale" ] }, article: article.reload.shared_payload }, status: :conflict
      end
    end

    private

    def authenticate_share
      @share = ArticleShare.authenticate(params[:id], request.headers["X-Share-Key"])
      render_error(:share, "not found", :not_found) unless @share
    end

    def valid_edit?(payload)
      payload.is_a?(ActionController::Parameters) &&
        payload.keys.sort == %w[body revision title] &&
        payload[:title].is_a?(String) && payload[:body].is_a?(String) &&
        payload[:revision].is_a?(Integer)
    end
  end
end

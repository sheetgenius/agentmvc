module Api
  class SharesController < ApplicationController
    before_action :find_share, only: %i[show update]

    def show
      render json: { article: @share.article.shared_json }
    end

    def update
      article = @share.article
      article.with_lock do
        fields = input(:article)
        unless fields.keys.sort == %w[body revision title] && fields[:title].is_a?(String) &&
            fields[:body].is_a?(String) && fields[:revision].is_a?(Integer)
          return render_error(:article, "is invalid", :unprocessable_entity)
        end
        if fields[:revision] != article.revision
          return render json: { errors: { revision: [ "is stale" ] }, article: article.shared_json }, status: :conflict
        end
        article.update!(fields.permit(:title, :body))
      end
      LiveRooms.updated(article)
      render json: { article: article.shared_json }
    end

    def live
      return head :bad_request unless WebSocket::Driver.websocket?(request.env)
      LiveSocket.new(request.env, params[:id]).start
      head :ok
    end

    private

    def find_share
      @share = Share.authorized(params[:id], request.headers["X-Share-Key"])
      render_error(:share, "not found", :not_found) unless @share
    end
  end
end

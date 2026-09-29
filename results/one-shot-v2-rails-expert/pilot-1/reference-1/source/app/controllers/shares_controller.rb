class SharesController < ApplicationController
  def create
    article = author_article!
    share, key, old = ArticleShare.issue!(article)
    LiveRooms.revoked(old)
    render json: { share: { id: share.id, key: key } }, status: :created
  end
  def destroy
    article = author_article!
    ids = article.with_lock do
      active = article.article_shares.active
      active.pluck(:id).tap { active.update_all(revoked_at: Time.current) }
    end
    LiveRooms.revoked(ids)
    head :no_content
  end
  def show
    share = share!
    render json: { article: share.article.shared_json }
  end
  def update
    share = share!
    input = object!(:article)
    required = %w[title body revision]
    raise Failure.new(422, :article, "is invalid") unless input.keys.sort == required.sort && input[:title].is_a?(String) && input[:body].is_a?(String)
    ArticleCommit.call(share.article, input.to_unsafe_h, expected: input[:revision], representation: ->(a) { a.shared_json }, share: share, key: request.headers["X-Share-Key"])
    render json: { article: share.article.shared_json }
  end
  def live
    LiveSocket.open(request.env, params[:id])
  end
  private
  def share!
    share = ArticleShare.active.find_by(id: params[:id])
    raise Failure.new(404, :share, "not found") unless share&.valid_key?(request.headers["X-Share-Key"])
    share
  end
end

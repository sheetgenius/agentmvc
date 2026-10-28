class CommentsController < ApplicationController
  def index
    article = article!
    comments = article.comments.order(created_at: :desc, id: :desc).includes(:author)
    comments = comments.limit((Integer(param(:limit)) rescue 100).clamp(0, 100)) if params.key?(:limit)
    comments = comments.offset((Integer(param(:offset)) rescue 0).clamp(0, 1_000_000)) if params.key?(:offset)
    comments = comments.to_a
    followed = @current_user ? Follow.where(follower_id: @current_user.id, followed_id: comments.map(&:author_id)).pluck(:followed_id).to_set : nil
    render json: { comments: comments.map { |comment| comment_json(comment, followed) } }
  end

  def create
    require_user!
    article = public_article!
    comment = article.comments.create!(author: @current_user, body: string_cast(object!(:comment)["body"]))
    render json: { comment: comment_json(comment) }, status: :created
  end

  def destroy
    require_user!
    article = article!
    comment = article.comments.find_by(id: param(:id)) || (raise Failure.new(404, :comment, "not found"))
    raise Failure.new(403, :comment, "forbidden") unless comment.author_id == @current_user.id
    comment.destroy!
    head :no_content
  end

  private
  def comment_json(comment, followed = nil)
    { id: comment.id, createdAt: comment.created_at.iso8601(3), updatedAt: comment.updated_at.iso8601(3),
      body: comment.body, author: profile_json(comment.author, followed) }
  end
end

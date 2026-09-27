class Export < ApplicationRecord
  belongs_to :user

  def status
    completed_at? ? "done" : "pending"
  end

  def build!
    with_lock do
      next if completed_at?

      articles = user.articles.order(:created_at, :id).includes(:tags).to_a
      comment_counts = Comment.where(article_id: articles.map(&:id)).group(:article_id).count

      update!(articles: articles.map { |article|
        article.attributes.slice("slug", "title", "description", "body", "status").merge(
          "tagList" => article.tags.map(&:name), "commentsCount" => comment_counts.fetch(article.id, 0)
        )
      }, completed_at: Time.current)
    end
  end
end

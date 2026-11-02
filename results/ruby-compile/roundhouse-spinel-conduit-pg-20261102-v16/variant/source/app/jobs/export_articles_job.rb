class ExportArticlesJob < ApplicationJob
  def perform(id)
    export = ArticleExport.find_by(id: id)
    return unless export && export.status == "pending"
    # Roundhouse retains computed select aliases through [], without named getters.
    articles = Article.where(author_id: export.user_id).order(:created_at, :id)
      .left_joins(:comments).select("articles.*, COUNT(comments.id) AS comments_total")
      .group("articles.id").map do |article|
      article.attributes.slice("slug", "title", "description", "body", "status").merge(
        "tagList" => article.tag_list, "commentsCount" => article["comments_total"].to_i
      )
    end
    export.with_lock do
      export.update!(status: "done", articles: articles, completed_at: Time.current) if export.status == "pending"
    end
  end
end

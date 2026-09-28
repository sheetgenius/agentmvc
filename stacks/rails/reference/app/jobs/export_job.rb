class ExportJob < ActiveJob::Base
  def perform(export)
    articles = export.user.articles.order(:created_at, :id).map do |article|
      { slug: article.slug, title: article.title, description: article.description, body: article.body,
        tagList: article.tags, status: article.status, commentsCount: article.comments.count }
    end
    export.update!(articles: articles, status: "done", completed_at: Time.current)
  end
end

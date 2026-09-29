class TagsController < ApplicationController
  def index
    tags = Article.published.connection.select_values("SELECT DISTINCT unnest(tag_list) FROM articles WHERE status = 'published' ORDER BY 1")
    render json: { tags: tags }
  end
end

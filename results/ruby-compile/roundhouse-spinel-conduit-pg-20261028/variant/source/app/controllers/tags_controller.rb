class TagsController < ApplicationController
  def index
    # Roundhouse lacks relation.connection and Connection#select_values.
    tags = Article.connection.select_all("SELECT DISTINCT unnest(tag_list) AS tag FROM articles WHERE status = 'published' ORDER BY 1").to_a.map { |row| row["tag"] }
    render json: { tags: tags }
  end
end

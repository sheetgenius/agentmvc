module Api
  class TagsController < ApplicationController
    def index
      render json: { tags: Article.published.pluck(:tags).flatten.uniq.sort }
    end
  end
end

module Api
  class TagsController < ApplicationController
    def index
      @tags = Tag.joins(:articles).merge(Article.published).distinct.order(:name).pluck(:name)
    end
  end
end

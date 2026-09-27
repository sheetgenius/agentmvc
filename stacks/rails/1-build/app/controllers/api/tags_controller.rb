module Api
  class TagsController < ApplicationController
    def index
      @tags = Tag.order(:name).pluck(:name)
    end
  end
end

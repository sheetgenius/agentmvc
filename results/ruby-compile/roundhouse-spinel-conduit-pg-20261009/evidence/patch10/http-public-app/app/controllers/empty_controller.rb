class EmptyController < ApplicationController
  def show
    head :no_content, content_type: "application/json"
  end
  def cached
    head :not_modified, content_type: "application/json"
  end
end

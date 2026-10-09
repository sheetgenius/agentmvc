class EmptyController < ApplicationController
  def show
    head :no_content, content_type: "application/json"
  end
end

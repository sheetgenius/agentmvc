class EmptyController < ActionController::API
  def show
    head :no_content, content_type: "application/json"
  end
end

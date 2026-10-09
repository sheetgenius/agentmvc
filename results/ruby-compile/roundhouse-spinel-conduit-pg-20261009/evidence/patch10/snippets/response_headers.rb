class WidgetsController < ActionController::API
  after_action { response.set_header("X-Mode", "api") }
  def show
    render json: { ready: true }
  end
end

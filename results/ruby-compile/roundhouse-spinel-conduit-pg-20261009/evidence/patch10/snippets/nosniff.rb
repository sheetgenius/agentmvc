class WidgetsController < ActionController::API
  def show
    render json: { ready: true }
  end
end

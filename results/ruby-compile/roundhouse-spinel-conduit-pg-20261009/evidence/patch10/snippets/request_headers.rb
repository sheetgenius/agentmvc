class RequestsController < ActionController::API
  def show
    render json: { key: request.headers["X-Key"], token: request.authorization }
  end
end

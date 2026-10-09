class RequestsController < ActionController::API
  def show
    render json: { peer: request.remote_ip }
  end
end

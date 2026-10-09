class RequestsController < ApplicationController
  def show
    render json: { key: request.headers["X-Key"], authorization: request.authorization, peer: request.remote_ip }
  end
end

class CallbacksController < ActionController::API
  before_action { render json: { stage: "filter" }, status: 409 }
  def show
    render json: { stage: "action" }
  end
end

class DatesController < ActionController::API
  def show
    render json: { at: Time.current }
  end
end

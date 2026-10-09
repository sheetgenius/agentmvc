class StatusController < ActionController::API
  def code
    202
  end
  def show
    head code
  end
end

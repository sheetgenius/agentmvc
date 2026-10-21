class ProbeController < ActionController::API
  rescue_from ActionDispatch::Http::Parameters::ParseError do
    render json: { error: "parse" }, status: :bad_request
  end
  def create
    params.require(:probe)
    render json: { ok: true }
  end
end

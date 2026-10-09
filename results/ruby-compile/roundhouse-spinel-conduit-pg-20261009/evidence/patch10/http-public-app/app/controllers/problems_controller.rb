class ProblemsController < ApplicationController
  def show
    widget = Widget.new
    widget.valid?
    render json: { errors: widget.errors.to_hash }
  end
end

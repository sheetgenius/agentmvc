class FormsController < ApplicationController
  def show
    form = SignupForm.new
    form.valid?
    render json: { errors: form.errors.messages }
  end
end

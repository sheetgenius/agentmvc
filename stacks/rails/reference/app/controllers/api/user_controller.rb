module Api
  class UserController < ApplicationController
    before_action :authenticate_user!

    def show
      render json: { user: presenter.user(current_user) }
    end

    def update
      fields = input(:user)
      if fields.key?(:password) && (!fields[:password].is_a?(String) || fields[:password].length < 8)
        return render_error(:password, "is invalid", :unprocessable_entity)
      end
      current_user.update!(fields.permit(:email, :username, :password, :bio, :image))
      render json: { user: presenter.user(current_user) }
    end
  end
end

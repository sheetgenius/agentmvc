module Api
  class UsersController < ApplicationController
    before_action :authenticate_user!, only: [ :show, :update ]

    def create
      @user = User.create!(string_params(:user, :username, :email, :password))
      render :show, status: :created
    end

    def show
      @user = current_user
    end

    def update
      @user = current_user
      attributes = string_params(:user, :username, :email, :password, :bio, :image)
      return render_error(:password, "can't be blank", :unprocessable_content) if attributes.key?(:password) && attributes[:password].blank?

      @user.update!(attributes)
      render :show
    end
  end
end

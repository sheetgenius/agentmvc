module Api
  class ProfilesController < ApplicationController
    before_action :authenticate_user!, only: %i[follow unfollow]
    before_action :find_profile

    def show
      render_profile
    end

    def follow
      current_user.outgoing_follows.find_or_create_by!(followed: @user)
      render_profile
    end

    def unfollow
      current_user.outgoing_follows.where(followed: @user).delete_all
      render_profile
    end

    private

    def find_profile
      @user = User.find_by!(username: params[:username])
    rescue ActiveRecord::RecordNotFound
      render_error(:profile, "not found", :not_found)
    end

    def render_profile
      render json: { profile: presenter.profile(@user) }
    end
  end
end

module Api
  class ProfilesController < ApplicationController
    before_action :authenticate_user!, only: [ :follow, :unfollow ]
    before_action :set_profile

    def show; end

    def follow
      current_user.outgoing_follows.find_or_create_by!(followed: @profile)
      render :show
    end

    def unfollow
      current_user.outgoing_follows.where(followed: @profile).delete_all
      render :show
    end

    private

    def set_profile
      @profile = User.find_by!(username: params[:username])
    end
  end
end

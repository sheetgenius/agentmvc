class ProfilesController < ApplicationController
  def show
    render json: { profile: profile_json(profile!) }
  end
  def follow
    require_user!
    user = profile!
    Follow.find_or_create_by!(follower: @current_user, followed: user) unless user == @current_user
    render json: { profile: profile_json(user) }
  end
  def unfollow
    require_user!
    user = profile!
    Follow.where(follower: @current_user, followed: user).delete_all
    render json: { profile: profile_json(user) }
  end
  private
  def profile!
    User.find_by(username: params[:username]) || (raise Failure.new(404, :profile, "not found"))
  end
end

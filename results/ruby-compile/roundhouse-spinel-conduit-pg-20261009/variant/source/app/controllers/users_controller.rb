class UsersController < ApplicationController
  def create
    input = object!(:user)
    user = User.new(permitted(input, %i[username email password]))
    if user.save
      render json: { user: user_json(user) }, status: :created
    elsif user.errors.of_kind?(:username, :taken) || user.errors.of_kind?(:email, :taken)
      render json: { errors: user.errors.to_hash }, status: :conflict
    else
      render json: { errors: user.errors.to_hash }, status: :unprocessable_entity
    end
  end

  def login
    input = object!(:user)
    %i[email password].each do |field|
      raise Failure.new(422, field, "can't be blank") if input[field.to_s].blank?
    end
    email = input["email"]
    password = input["password"]
    raise Failure.new(422, :credentials, "invalid") unless email.is_a?(String) && password.is_a?(String)
    user = User.where("lower(email) = ?", email.downcase).first
    if user&.authenticate(password)
      render json: { user: user_json(user) }
    else
      LoginThrottle.fail!(email, request.remote_ip)
      raise Failure.new(401, :credentials, "invalid")
    end
  end

  def show
    require_user!
    render json: { user: user_json(@current_user) }
  end

  def update
    require_user!
    @current_user.update!(permitted(object!(:user), %i[username email password image bio]))
    render json: { user: user_json(@current_user) }
  end

  private

  def user_json(user)
    token = TokenCodec.encode({ sub: user.id, exp: 30.days.from_now.to_i }, Rails.application.secret_key_base)
    { email: user.email, token: token, username: user.username, bio: user.bio, image: user.image }
  end
end

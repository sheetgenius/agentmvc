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
      raise Failure.new(422, field, "can't be blank") if blank_value?(input[field.to_s])
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
    input = object!(:user)
    # Spinel workaround: direct writers avoid the crashing synthesized update! hash path.
    %w[username email password image bio].each do |name|
      next unless input.key?(name)
      value = input[name]
      next if value.is_a?(Hash) || value.is_a?(Array)
      value = string_cast(value)
      case name
      when "username" then @current_user.username = value
      when "email" then @current_user.email = value
      when "password" then @current_user.password = value
      when "image" then @current_user.image = value
      when "bio" then @current_user.bio = value
      end
    end
    @current_user.save!
    render json: { user: user_json(@current_user) }
  end

  private

  def user_json(user)
    token = TokenCodec.encode({ sub: user.id, exp: 30.days.from_now.to_i }, Rails.application.secret_key_base)
    { email: user.email, token: token, username: user.username, bio: user.bio, image: user.image }
  end
end

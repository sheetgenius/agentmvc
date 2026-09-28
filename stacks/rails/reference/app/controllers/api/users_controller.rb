module Api
  class UsersController < ApplicationController
    def create
      user = User.create!(input(:user).permit(:username, :email, :password))
      render json: { user: presenter.user(user) }, status: :created
    end

    def login
      fields = input(:user)
      %i[email password].each do |field|
        return render_error(field, "can't be blank", :unprocessable_entity) if fields[field].blank?
      end
      email = fields[:email]
      return render_error(:credentials, "invalid", :unauthorized) unless email.is_a?(String) && fields[:password].is_a?(String)
      attempts = Rails.cache.read("login:#{Digest::SHA256.hexdigest(email)}").to_i
      return render_error(:credentials, "invalid", :too_many_requests) if attempts >= 20
      user = User.find_by(email: email)
      unless user&.authenticate(fields[:password])
        Rails.cache.write("login:#{Digest::SHA256.hexdigest(email)}", attempts + 1, expires_in: 10.minutes)
        return render_error(:credentials, "invalid", :unauthorized)
      end
      Rails.cache.delete("login:#{Digest::SHA256.hexdigest(email)}")
      render json: { user: presenter.user(user) }
    end
  end
end

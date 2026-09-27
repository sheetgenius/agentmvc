module Api
  class SessionsController < ApplicationController
    before_action :set_credentials, only: :create
    rate_limit to: 20, within: 5.minutes, by: -> { "#{request.remote_ip}:#{@credentials[:email].to_s.downcase}" }, only: :create

    def create
      %i[email password].each do |field|
        return render_error(field, "can't be blank", :unprocessable_content) if @credentials[field].blank?
      end

      @user = User.find_by(email: @credentials[:email])
      return render_error(:credentials, "invalid", :unauthorized) unless @user&.authenticate(@credentials[:password])

      render "api/users/show"
    end

    private

    def set_credentials
      @credentials = string_params(:user, :email, :password)
    end
  end
end

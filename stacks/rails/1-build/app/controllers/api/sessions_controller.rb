module Api
  class SessionsController < ApplicationController
    def create
      credentials = params.require(:user).permit(:email, :password)
      %i[email password].each do |field|
        return render_error(field, "can't be blank", :unprocessable_content) if credentials[field].blank?
      end

      @user = User.find_by(email: credentials[:email])
      return render_error(:credentials, "invalid", :unauthorized) unless @user&.authenticate(credentials[:password])

      render "api/users/show"
    end
  end
end

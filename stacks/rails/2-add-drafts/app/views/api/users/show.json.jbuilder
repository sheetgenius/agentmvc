json.user do
  json.extract! @user, :email, :username, :bio, :image
  json.token @user.token
end

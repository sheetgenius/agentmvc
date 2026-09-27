json.extract! user, :username, :bio, :image
json.following !!current_user&.following?(user)

class Widget < ApplicationRecord
  has_secure_password
  def problems
    valid?
    errors.to_hash
  end
end
record = Widget.new(password: "ready", password_confirmation: "different")
record.problems

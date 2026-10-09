class Widget < ApplicationRecord
  validates :name, format: { with: /\A[a-z]+\z/ }
  def problems
    valid?
    errors.to_hash
  end
end

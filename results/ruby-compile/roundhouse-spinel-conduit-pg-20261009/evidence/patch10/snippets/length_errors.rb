class Widget < ApplicationRecord
  validates :name, length: { minimum: 3, maximum: 5 }
  def problems
    valid?
    errors.to_hash
  end
end

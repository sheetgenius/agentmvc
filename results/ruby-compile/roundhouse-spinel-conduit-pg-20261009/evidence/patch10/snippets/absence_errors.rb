class Widget < ApplicationRecord
  validates :name, absence: true
  def problems
    valid?
    errors.to_hash
  end
end

class Widget < ApplicationRecord
  validates :name, presence: true
  def problems
    valid?
    errors.to_hash
  end
end

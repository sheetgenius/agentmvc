class Widget < ApplicationRecord
  validates :amount, numericality: { greater_than: 2, less_than: 4, only_integer: true }
  def problems
    valid?
    errors.to_hash
  end
end

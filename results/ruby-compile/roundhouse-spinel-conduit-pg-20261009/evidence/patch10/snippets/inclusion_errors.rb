class Widget < ApplicationRecord
  validates :name, inclusion: { in: ["ready"] }
  def problems
    valid?
    errors.to_hash
  end
end

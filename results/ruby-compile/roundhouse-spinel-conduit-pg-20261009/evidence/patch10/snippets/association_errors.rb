class Owner < ApplicationRecord
end
class Widget < ApplicationRecord
  belongs_to :owner
  validates :owner, presence: true
  def problems
    valid?
    errors.to_hash
  end
end

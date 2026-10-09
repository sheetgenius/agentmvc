class Widget < ApplicationRecord
  validates :name, presence: true
  validate :reject_reserved
  def reject_reserved
    errors.add(:base, "reserved")
  end
end

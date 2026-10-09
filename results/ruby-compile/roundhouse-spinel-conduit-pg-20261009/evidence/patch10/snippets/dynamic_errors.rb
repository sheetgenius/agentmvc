class Widget < ApplicationRecord
  def self.attach_problem
    create!(name: "owner").errors.add(:name, message_text)
  end
  def self.message_text
    create!(name: "message")
    "reserved"
  end
end

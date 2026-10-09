class Widget < ApplicationRecord
  validates :name, presence: true
  def problems
    valid?
    errors.to_hash
  end
end
record = Widget.new(name: "")
record.problems
record.name = "ready"
raise unless record.problems.empty?

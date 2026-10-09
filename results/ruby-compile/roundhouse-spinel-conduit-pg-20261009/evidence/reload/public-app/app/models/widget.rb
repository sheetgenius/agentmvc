class Widget < ApplicationRecord
  def label
    name
  end
  def self.refreshed_label(id)
    find(id).reload.label
  end
end

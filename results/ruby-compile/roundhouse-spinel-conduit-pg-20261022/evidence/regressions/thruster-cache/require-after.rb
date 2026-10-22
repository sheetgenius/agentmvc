require_relative "source"
class Item
  attr_reader :value
  def initialize(value); @value = value; end
end
p [Item.new(1)].any? { |x| x.value == 1 }

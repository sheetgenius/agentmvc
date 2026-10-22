class Item
  attr_reader :value
  def initialize(value); @value = value; end
end
def items?(values); values.any? { |x| x.value == 1 }; end
p items?([Item.new(1)])
def matches?(value)
  value.split(",").any? { |candidate| candidate.strip == "a" }
end
p matches?(" a,b ")

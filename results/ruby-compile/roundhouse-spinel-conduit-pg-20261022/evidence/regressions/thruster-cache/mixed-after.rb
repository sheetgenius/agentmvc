class Item
  attr_reader :value
  def initialize(value); @value = value; end
end
def matches?(value)
  value.split(",").any? { |candidate| candidate.strip == "a" }
end
p matches?(" a,b ")
p [Item.new(1)].any? { |x| x.value == 1 }

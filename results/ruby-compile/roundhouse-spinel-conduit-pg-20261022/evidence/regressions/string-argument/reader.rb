class Header
  attr_reader :value
  def initialize(value); @value = value; end
end
def take(value); value; end
h = Header.new(+"Token a")
p take(h.value.to_s.delete_prefix("Token "))

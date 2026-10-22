class Header
  attr_reader :value
  def initialize; @value = +"Token a"; end
end
def take(value); value; end
def read(h)
  begin
    header = h.value.to_s
    return nil if header.empty?
    take(header.delete_prefix("Token "))
  rescue StandardError
    nil
  end
end
p read(Header.new)

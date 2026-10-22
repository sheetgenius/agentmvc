class Config
  attr_reader :key
  def initialize; @key = ENV.fetch("SECRET_KEY_BASE", "b"); end
end
class Header
  attr_reader :value
  def initialize; @value = +""; end
end
class Decoder
  def self.decode(token, secret); token + secret.to_s; end
end
h = Header.new
h.value << "Token a"
def read(h, c)
  header = h.value.to_s
  Decoder.decode(header.delete_prefix("Token "), c.key)
end
p read(h, Config.new)

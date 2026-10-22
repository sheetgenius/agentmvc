class Config
  attr_reader :key
  def initialize; @key = ENV.fetch("SECRET_KEY_BASE", "b"); end
end
def take(value, key); value + key; end
h = {"auth" => +"Token a"}
p take(h["auth"].delete_prefix("Token "), Config.new.key)

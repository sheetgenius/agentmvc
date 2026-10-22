class Decoder
  def self.decode(value, key); value + key; end
end
h = {"auth" => +"Token a"}
p Decoder.decode(h["auth"].delete_prefix("Token "), "b")

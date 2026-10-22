class Decoder
 def self.decode(token, secret); token << secret.to_s; token; end
end
h = {"auth" => +"Token a"}
p Decoder.decode(h["auth"].delete_prefix("Token "), "b")

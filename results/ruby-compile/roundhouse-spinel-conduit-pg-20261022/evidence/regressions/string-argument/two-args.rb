def take(value, key); value + key; end
h = {"auth" => +"Token a"}
k = +"b"
p take(h["auth"].delete_prefix("Token "), k)

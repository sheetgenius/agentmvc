def take(value); value << "b"; end
h = {"auth" => +"Token a"}
p take(h["auth"].delete_prefix("Token "))

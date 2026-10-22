def take(value); value; end
h = {"auth" => +"Token a"}
p take(h["auth"].delete_prefix("Token "))

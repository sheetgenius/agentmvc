def take(value); value; end
s = +"Token a"
p take(s.delete_prefix("Token "))

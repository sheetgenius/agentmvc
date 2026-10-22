def take(value); value; end
h = {"auth" => +"Token a"}
begin
  p take(h["auth"].delete_prefix("Token "))
rescue StandardError
  p :error
end

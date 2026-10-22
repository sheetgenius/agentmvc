def take(value); value; end
h = {"auth" => +"Token a"}
Thread.new { p take(h["auth"].delete_prefix("Token ")) }.join

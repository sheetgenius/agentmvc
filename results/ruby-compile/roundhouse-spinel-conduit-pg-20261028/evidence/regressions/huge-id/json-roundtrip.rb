require "json"
value = {"id" => "9" * 100, "user_id" => 1}
text = JSON.generate(value)
p text
p JSON.parse(text)

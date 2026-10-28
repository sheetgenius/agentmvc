def text_of(scalar)
  if scalar == true
    "1"
  elsif scalar == false
    "0"
  elsif scalar.is_a?(Float)
    scalar.to_i.to_s
  else
    scalar.to_s
  end
end
p text_of("9" * 100)
p text_of(1.9)
p text_of(true)
p text_of(false)
p text_of(42)

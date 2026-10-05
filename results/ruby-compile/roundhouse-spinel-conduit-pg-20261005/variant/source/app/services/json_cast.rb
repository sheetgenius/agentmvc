# Compile variant: Active Model's string cast for typed JSON values (Rails applies it on assignment).
class JsonCast
  def self.string(value)
    return nil if value.nil?
    return "t" if value == true
    return "f" if value == false
    value.is_a?(String) ? value : value.to_s
  end
end

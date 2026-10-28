module ActiveRecord
  def self.integer_query_value(text, limit)
    value = text.lstrip
    negative = value.start_with?("-")
    value = value.sub(/\A[+-]/, "")
    return "NULL" unless value.match?(/\A[0-9]/)
    digits = ""
    i = 0
    while i < value.length
      char = value[i, 1]
      if char.match?(/\A[0-9]\z/)
        digits = digits + char
      elsif char == "_" && i + 1 < value.length && value[i + 1, 1].match?(/\A[0-9]\z/)
        # Ruby to_i accepts a single underscore between digits.
      else
        break
      end
      i += 1
    end
    digits = digits.sub(/\A0+/, "")
    digits = "0" if digits.empty?
    bound = if limit == 4
      negative ? "2147483648" : "2147483647"
    else
      negative ? "9223372036854775808" : "9223372036854775807"
    end
    return "" if digits.length > bound.length
    return "" if digits.length == bound.length && digits > bound
    negative && digits != "0" ? "-#{digits}" : digits
  end
end
p ActiveRecord.integer_query_value("9" * 100, 8)
p ActiveRecord.integer_query_value("42", 8)

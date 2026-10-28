def each_value(list)
  list.each { |item| yield item }
end
each_value(["9" * 100, 1, :a]) { |v| puts v }

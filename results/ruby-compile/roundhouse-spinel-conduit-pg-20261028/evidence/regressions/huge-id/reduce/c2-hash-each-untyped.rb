def conds(hash)
  parts = []
  hash.each { |key, val| parts << "#{key}=#{val}" }
  parts.join(" AND ")
end
puts conds({ id: "9" * 100, n: 1 })
puts conds({ id: 1.5, n: nil })

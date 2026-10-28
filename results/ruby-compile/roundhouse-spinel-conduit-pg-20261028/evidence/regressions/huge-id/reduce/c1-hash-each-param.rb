def conds(hash)
  parts = []
  hash.each do |key, val|
    parts << "#{key}=#{val}"
  end
  parts.join(" AND ")
end
puts conds({ id: "9" * 100 })
puts conds({ "user_id" => 1 })

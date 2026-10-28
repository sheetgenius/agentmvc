class Rel
  def initialize; @parts = []; end
  def where(hash)
    hash.each do |key, val|
      if val.is_a?(Hash)
        val.each { |col, v| @parts << "#{key}.#{col} = #{v}" }
      else
        @parts << "#{key} = #{val}"
      end
    end
    @parts.join(" AND ")
  end
end
params = { "id" => "9" * 100, "page" => 2 }
puts Rel.new.where(id: params["id"])
puts Rel.new.where(comments: { id: 1 })

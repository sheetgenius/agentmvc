class Holder
  def initialize
    @fields = {}
    @fields["a"] = +""
    @fields["a"] << "x"
    puts @fields["a"]
  end
end
Holder.new

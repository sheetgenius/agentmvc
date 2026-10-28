def show(h)
  h.each { |k, v| puts "#{k}: #{v}" }
end
show({ id: "9" * 100 })
show([[:a, 1]])

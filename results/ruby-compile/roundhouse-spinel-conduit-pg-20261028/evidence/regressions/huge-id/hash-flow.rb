def take(attrs)
  puts attrs[:id].to_s
end
def arbitrary(x); x; end
take({ id: arbitrary("9" * 100), user_id: 1 })
take({ id: arbitrary(1), user_id: 2 })

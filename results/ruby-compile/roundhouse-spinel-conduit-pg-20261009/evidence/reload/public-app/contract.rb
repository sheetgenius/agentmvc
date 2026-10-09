require_relative "boot"
Db.configure(":memory:")
Db.exec("CREATE TABLE widgets (id INTEGER PRIMARY KEY, name TEXT)")
widget = Widget.create!(name: "fresh")
raise "receiver lost" unless Widget.refreshed_label(widget.id) == "fresh"
puts "native reload receiver: PASS"

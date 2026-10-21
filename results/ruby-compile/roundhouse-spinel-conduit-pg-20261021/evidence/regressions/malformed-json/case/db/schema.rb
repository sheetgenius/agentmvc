ActiveRecord::Schema.define do
  create_table "posts", force: :cascade do |t|
    t.string "body", null: false
  end
end

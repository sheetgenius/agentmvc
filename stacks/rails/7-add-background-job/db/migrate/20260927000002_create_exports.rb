class CreateExports < ActiveRecord::Migration[8.1]
  def change
    create_table :exports do |t|
      t.references :user, null: false, foreign_key: true
      t.jsonb :articles
      t.datetime :completed_at
      t.timestamps
    end
  end
end

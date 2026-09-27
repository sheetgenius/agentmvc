class AddDraftsToArticles < ActiveRecord::Migration[8.1]
  def change
    add_column :articles, :status, :string, default: "published", null: false
    add_column :articles, :published_at, :datetime
    add_column :articles, :revision, :integer, default: 1, null: false
  end
end

class CreateArticleShares < ActiveRecord::Migration[8.1]
  def change
    create_table :article_shares do |t|
      t.references :article, null: false, foreign_key: true, index: { unique: true }
      t.string :public_id, null: false, index: { unique: true }
      t.string :key_digest, null: false
      t.timestamps
    end
  end
end

class CreateConduit < ActiveRecord::Migration[8.1]
  def change
    create_table :users do |t|
      t.string :username, null: false
      t.string :email, null: false
      t.string :password_digest, null: false
      t.text :bio
      t.string :image
      t.timestamps
    end
    add_index :users, 'lower(username)', unique: true
    add_index :users, 'lower(email)', unique: true
    create_table :follows, id: false do |t|
      t.references :follower, null: false, foreign_key: { to_table: :users }
      t.references :followed, null: false, foreign_key: { to_table: :users }
    end
    add_index :follows, [ :follower_id, :followed_id ], unique: true
    add_check_constraint :follows, 'follower_id <> followed_id', name: 'no_self_follow'
    create_table :articles do |t|
      t.references :author, null: false, foreign_key: { to_table: :users }
      t.string :slug, null: false
      t.string :title, null: false
      t.text :description, null: false
      t.text :body, null: false
      t.text :tag_list, array: true, default: [], null: false
      t.string :status, default: 'published', null: false
      t.datetime :published_at
      t.integer :revision, default: 1, null: false
      t.timestamps
    end
    add_index :articles, :slug, unique: true
    add_index :articles, [ :status, :created_at ]
    add_index :articles, :tag_list, using: :gin
    add_check_constraint :articles, "status IN ('draft', 'published') AND ((status = 'draft' AND published_at IS NULL) OR (status = 'published' AND published_at IS NOT NULL))", name: 'article_lifecycle'
    add_check_constraint :articles, 'revision > 0', name: 'positive_revision'
    create_table :favorites, id: false do |t|
      t.references :user, null: false, foreign_key: true
      t.references :article, null: false, foreign_key: true
    end
    add_index :favorites, [ :user_id, :article_id ], unique: true
    create_table :comments do |t|
      t.references :article, null: false, foreign_key: true
      t.references :author, null: false, foreign_key: { to_table: :users }
      t.text :body, null: false
      t.timestamps
    end
    create_table :article_exports do |t|
      t.references :user, null: false, foreign_key: true
      t.string :status, default: 'pending', null: false
      t.jsonb :articles
      t.datetime :completed_at
      t.timestamps
    end
    add_check_constraint :article_exports, "(status = 'pending' AND articles IS NULL AND completed_at IS NULL) OR (status = 'done' AND articles IS NOT NULL AND completed_at IS NOT NULL)", name: 'export_state'
    create_table :article_shares, id: :uuid do |t|
      t.references :article, null: false, foreign_key: true, index: false
      t.string :key_hash, null: false
      t.datetime :revoked_at
      t.timestamps
    end
    add_index :article_shares, :article_id, unique: true, where: 'revoked_at IS NULL'
  end
end

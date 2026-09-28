class CreateConduit < ActiveRecord::Migration[8.1]
  def change
    create_table :users do |t|
      t.string :username, :email, :password_digest, null: false
      t.text :bio, :image
      t.timestamps
    end
    add_index :users, :username, unique: true
    add_index :users, :email, unique: true

    create_table :follows do |t|
      t.references :follower, null: false, foreign_key: { to_table: :users }
      t.references :followed, null: false, foreign_key: { to_table: :users }
    end
    add_index :follows, [ :follower_id, :followed_id ], unique: true

    create_table :articles do |t|
      t.references :author, null: false, foreign_key: { to_table: :users }
      t.string :slug, :title, null: false
      t.text :description, :body, null: false
      t.text :tags, array: true, null: false, default: []
      t.string :status, null: false, default: "published"
      t.datetime :published_at
      t.integer :revision, null: false, default: 1
      t.timestamps
    end
    add_index :articles, :slug, unique: true

    create_table :comments do |t|
      t.references :article, null: false, foreign_key: true
      t.references :author, null: false, foreign_key: { to_table: :users }
      t.text :body, null: false
      t.timestamps
    end

    create_table :favorites do |t|
      t.references :user, null: false, foreign_key: true
      t.references :article, null: false, foreign_key: true
    end
    add_index :favorites, [ :user_id, :article_id ], unique: true

    create_table :exports do |t|
      t.references :user, null: false, foreign_key: true
      t.string :status, null: false, default: "pending"
      t.jsonb :articles
      t.datetime :completed_at
      t.timestamps
    end

    create_table :shares do |t|
      t.references :article, null: false, foreign_key: true, index: { unique: true }
      t.string :public_id, :key_digest, null: false
      t.timestamps
    end
    add_index :shares, :public_id, unique: true
  end
end

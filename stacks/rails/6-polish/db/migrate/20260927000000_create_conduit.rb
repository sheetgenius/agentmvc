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
    add_index :users, :username, unique: true
    add_index :users, :email, unique: true

    create_table :articles do |t|
      t.references :author, null: false, foreign_key: { to_table: :users }
      t.string :slug, null: false
      t.string :title, null: false
      t.text :description, null: false
      t.text :body, null: false
      t.timestamps
    end
    add_index :articles, :slug, unique: true

    create_table :comments do |t|
      t.references :article, null: false, foreign_key: true
      t.references :author, null: false, foreign_key: { to_table: :users }
      t.text :body, null: false
      t.timestamps
    end

    create_table :tags do |t|
      t.string :name, null: false
    end
    add_index :tags, :name, unique: true

    create_table :article_tags do |t|
      t.references :article, null: false, foreign_key: true
      t.references :tag, null: false, foreign_key: true
    end
    add_index :article_tags, [ :article_id, :tag_id ], unique: true

    create_table :favorites do |t|
      t.references :user, null: false, foreign_key: true
      t.references :article, null: false, foreign_key: true
    end
    add_index :favorites, [ :user_id, :article_id ], unique: true

    create_table :follows do |t|
      t.references :follower, null: false, foreign_key: { to_table: :users }
      t.references :followed, null: false, foreign_key: { to_table: :users }
    end
    add_index :follows, [ :follower_id, :followed_id ], unique: true
  end
end

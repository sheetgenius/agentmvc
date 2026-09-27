class User < ApplicationRecord
  has_secure_password

  has_many :articles, foreign_key: :author_id, dependent: :destroy, inverse_of: :author
  has_many :comments, foreign_key: :author_id, dependent: :destroy, inverse_of: :author
  has_many :favorites, dependent: :destroy
  has_many :favorite_articles, through: :favorites, source: :article
  has_many :outgoing_follows, class_name: "Follow", foreign_key: :follower_id, dependent: :destroy
  has_many :followed_users, through: :outgoing_follows, source: :followed
  has_many :incoming_follows, class_name: "Follow", foreign_key: :followed_id, dependent: :destroy

  validates :username, :email, presence: true, uniqueness: true
  validates :password, length: { minimum: 8 }, if: -> { password.present? }
  normalizes :bio, :image, with: ->(value) { value.presence }

  def following?(user)
    followed_users.exists?(user.id)
  end

  def token
    JWT.encode({ sub: id, exp: 30.days.from_now.to_i }, Rails.application.secret_key_base, "HS256")
  end
end

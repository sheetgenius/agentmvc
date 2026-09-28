class User < ApplicationRecord
  has_secure_password
  has_many :articles, foreign_key: :author_id, dependent: :destroy, inverse_of: :author
  has_many :comments, foreign_key: :author_id, dependent: :destroy
  has_many :favorites, dependent: :destroy
  has_many :exports, dependent: :destroy
  has_many :outgoing_follows, class_name: "Follow", foreign_key: :follower_id, dependent: :destroy
  has_many :followed_users, through: :outgoing_follows, source: :followed
  validates :username, :email, presence: true, uniqueness: true
  validates :password, length: { minimum: 8 }, if: -> { password.present? }
  before_validation do
    self.bio = nil if bio.blank?
    self.image = nil if image.blank?
  end
end

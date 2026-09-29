class User < ApplicationRecord
  before_validation :normalize_optional_fields
  has_secure_password
  has_many :articles, foreign_key: :author_id, dependent: :destroy
  has_many :article_exports, dependent: :destroy
  validates :username, :email, presence: true
  validates :username, uniqueness: { case_sensitive: false }
  validates :email, uniqueness: { case_sensitive: false }
  validates :password, length: { minimum: 8 }, if: -> { password.present? }
  validate :password_is_present_when_supplied

  def normalize_optional_fields
    self.bio = nil if bio == ""
    self.image = nil if image == ""
  end

  def password_is_present_when_supplied
    errors.add(:password, "can't be blank") if @password_supplied && password.blank?
  end

  def password=(value)
    @password_supplied = true
    super
  end
end

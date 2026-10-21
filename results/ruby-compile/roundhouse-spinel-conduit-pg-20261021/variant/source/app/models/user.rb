class User < ApplicationRecord
  before_validation :normalize_optional_fields
  has_secure_password
  has_many :articles, foreign_key: :author_id, dependent: :destroy
  has_many :article_exports, dependent: :destroy
  validates :username, :email, presence: true
  validates :username, uniqueness: { case_sensitive: false }
  validates :email, uniqueness: { case_sensitive: false }
  validate :password_has_minimum_length
  validate :password_is_present_when_supplied

  def normalize_optional_fields
    self.bio = nil if bio == ""
    self.image = nil if image == ""
  end

  # Preserve the conditional that the validation macro ingest drops.
  def password_has_minimum_length
    errors.add(:password, "is too short (minimum is 8 characters)") if password.present? && password.length < 8
  end

  def password_is_present_when_supplied
    errors.add(:password, "can't be blank") if @password_supplied && password.blank?
  end

  def password=(value)
    @password_supplied = true
    super
  end
end

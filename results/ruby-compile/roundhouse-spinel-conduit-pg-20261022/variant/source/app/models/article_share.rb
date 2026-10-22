require "digest"
class ArticleShare < ApplicationRecord
  belongs_to :article
  scope :active, -> { where(revoked_at: nil) }

  def self.issue!(article)
    key = SecureRandom.urlsafe_base64(32)
    share = nil
    old = nil
    article.with_lock do
      old = active.where(article: article).pluck(:id)
      active.where(article: article).update_all(revoked_at: Time.current)
      share = create!(article: article, key_hash: Digest::SHA256.hexdigest(key))
    end
    [ share, key, old ]
  end

  def valid_key?(key)
    return false unless revoked_at.nil? && key.is_a?(String)
    hash = Digest::SHA256.hexdigest(key)
    ActiveSupport::SecurityUtils.secure_compare(key_hash, hash)
  end
end

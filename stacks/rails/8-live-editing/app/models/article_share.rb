class ArticleShare < ApplicationRecord
  belongs_to :article

  after_destroy_commit -> { ShareRoom.revoke(public_id) }

  def self.issue!(article)
    key = SecureRandom.urlsafe_base64(32)
    share = article.create_article_share!(
      public_id: SecureRandom.urlsafe_base64(18),
      key_digest: Digest::SHA256.hexdigest(key)
    )
    [ share, key ]
  end

  def self.authenticate(id, key)
    return unless key.is_a?(String)

    share = find_by(public_id: id)
    return unless share && ActiveSupport::SecurityUtils.secure_compare(share.key_digest, Digest::SHA256.hexdigest(key))

    share
  end
end

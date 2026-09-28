class Share < ApplicationRecord
  belongs_to :article
  before_validation { self.public_id ||= SecureRandom.urlsafe_base64(12) }

  def self.authorized(id, key)
    share = find_by(public_id: id)
    return unless share && key.is_a?(String) && key.bytesize < 512
    share if ActiveSupport::SecurityUtils.secure_compare(share.key_digest, Digest::SHA256.hexdigest(key))
  end

  def rotate!
    key = SecureRandom.urlsafe_base64(32)
    update!(public_id: SecureRandom.urlsafe_base64(12), key_digest: Digest::SHA256.hexdigest(key))
    key
  end
end

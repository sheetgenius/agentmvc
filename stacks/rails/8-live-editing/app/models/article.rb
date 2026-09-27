class Article < ApplicationRecord
  enum :status, { draft: "draft", published: "published" }, validate: { message: "is invalid" }

  belongs_to :author, class_name: "User"
  has_many :comments, dependent: :destroy
  has_many :favorites, dependent: :destroy
  has_many :article_tags, -> { order(:id) }, dependent: :destroy
  has_many :tags, through: :article_tags
  has_one :article_share, dependent: :destroy

  validates :title, :description, :body, presence: true
  before_validation :set_slug, if: :will_save_change_to_title?
  before_save :set_published_at, if: -> { published? && published_at.nil? }
  after_update_commit :broadcast_shared_update, if: :saved_change_to_revision?

  scope :visible_to, ->(user) { published.or(where(author: user)) }
  scope :by_author, ->(username) { joins(:author).where(users: { username: username }) }
  scope :tagged, ->(name) { joins(:tags).where(tags: { name: name }) }
  scope :favorited_by, ->(username) {
    where(id: Favorite.joins(:user).where(users: { username: username }).select(:article_id))
  }
  scope :recent, -> { order(created_at: :desc, id: :desc) }

  def publish!
    with_lock do
      update!(status: :published, revision: revision + 1) if draft?
    end
  end

  def revise!(attributes, expected_revision: nil, tag_list: nil)
    with_lock do
      next false if expected_revision && expected_revision != revision

      update!(attributes.merge(revision: revision + 1))
      replace_tags(tag_list) if tag_list
      true
    end
  end

  def replace_tags(names)
    self.tags = names.uniq.map { |name| Tag.find_or_create_by!(name: name) }
  end

  def favorited_by?(user)
    return false unless user

    favorites.loaded? ? favorites.any? { |favorite| favorite.user_id == user.id } : favorites.exists?(user: user)
  end

  def shared_payload
    { slug: slug, title: title, body: body, revision: revision }
  end

  private

  def set_slug
    self.slug = "#{title.to_s.parameterize}-#{SecureRandom.hex(6)}" if title.present?
  end

  def set_published_at
    self.published_at = Time.current
  end

  def broadcast_shared_update
    ShareRoom.updated(article_share.public_id, shared_payload) if article_share
  end
end

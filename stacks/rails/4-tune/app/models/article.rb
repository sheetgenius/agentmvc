class Article < ApplicationRecord
  enum :status, { draft: "draft", published: "published" }, validate: { message: "is invalid" }

  belongs_to :author, class_name: "User"
  has_many :comments, dependent: :destroy
  has_many :favorites, dependent: :destroy
  has_many :article_tags, -> { order(:id) }, dependent: :destroy
  has_many :tags, through: :article_tags

  validates :title, :description, :body, presence: true
  before_validation :set_slug, if: :will_save_change_to_title?
  before_save :set_published_at, if: -> { published? && published_at.nil? }

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

  def favorited_by?(user)
    return false unless user

    favorites.loaded? ? favorites.any? { |favorite| favorite.user_id == user.id } : favorites.exists?(user: user)
  end

  private

  def set_slug
    self.slug = "#{title.to_s.parameterize}-#{SecureRandom.hex(6)}" if title.present?
  end

  def set_published_at
    self.published_at = Time.current
  end
end

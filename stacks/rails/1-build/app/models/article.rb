class Article < ApplicationRecord
  belongs_to :author, class_name: "User"
  has_many :comments, dependent: :destroy
  has_many :favorites, dependent: :destroy
  has_many :article_tags, -> { order(:id) }, dependent: :destroy
  has_many :tags, through: :article_tags

  validates :title, :description, :body, presence: true
  before_validation :set_slug, if: :will_save_change_to_title?

  scope :by_author, ->(username) { joins(:author).where(users: { username: username }) }
  scope :tagged, ->(name) { joins(:tags).where(tags: { name: name }) }
  scope :favorited_by, ->(username) {
    where(id: Favorite.joins(:user).where(users: { username: username }).select(:article_id))
  }
  scope :recent, -> { order(created_at: :desc, id: :desc) }

  private

  def set_slug
    self.slug = "#{title.to_s.parameterize}-#{SecureRandom.hex(6)}" if title.present?
  end
end

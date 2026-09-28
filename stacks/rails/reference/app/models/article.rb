class Article < ApplicationRecord
  belongs_to :author, class_name: "User"
  has_many :comments, dependent: :destroy
  has_many :favorites, dependent: :destroy
  has_one :share, dependent: :destroy
  enum :status, { draft: "draft", published: "published" }, validate: { message: "is invalid" }
  scope :visible_to, ->(viewer) { viewer ? where(status: "published").or(where(author: viewer)) : published }
  scope :authored_by, ->(name) { where(author: User.where(username: name)) }
  scope :favorited_by, ->(name) { where(id: Favorite.where(user: User.where(username: name)).select(:article_id)) }
  scope :tagged_with, ->(tag) { where("? = ANY(tags)", tag) }
  validates :title, :description, :body, presence: true
  validate :valid_tags
  before_validation :assign_slug, if: :will_save_change_to_title?
  before_create { self.published_at = Time.current if published? }
  before_update { self.revision += 1 }

  def shared_json
    slice(:slug, :title, :body, :revision).symbolize_keys
  end

  private

  def valid_tags
    errors.add(:tagList, "is invalid") unless tags.is_a?(Array) && tags.all? { |tag| tag.is_a?(String) }
  end

  def assign_slug
    base = title.to_s.parameterize.presence || "article"
    self.slug = base
    self.slug = "#{base}-#{SecureRandom.hex(4)}" if Article.where(slug: base).where.not(id: id).exists?
  end
end

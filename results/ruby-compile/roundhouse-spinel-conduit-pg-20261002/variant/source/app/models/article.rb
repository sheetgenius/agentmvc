class Article < ApplicationRecord
  belongs_to :author, class_name: "User"
  has_many :comments, dependent: :destroy
  has_many :favorites, dependent: :delete_all
  has_many :article_shares, dependent: :destroy
  validates :title, :description, :body, presence: true
  validates :status, inclusion: { in: %w[draft published] }
  validates :slug, uniqueness: true
  scope :published, -> { where(status: "published") }
  scope :visible_to, ->(user) { where(status: "published").or(where(author_id: user&.id)) }

  def self.slug_for(title)
    "#{title.to_s.parameterize.presence || 'article'}-#{SecureRandom.hex(5)}"
  end

  def shared_json
    { slug: slug, title: title, body: body, revision: revision }
  end

  def publish!
    published = false
    with_lock do
      if status == "draft"
        update!(status: "published", published_at: Time.current, revision: revision + 1)
        published = true
      end
    end
    LiveRooms.updated(self) if published
  end
end

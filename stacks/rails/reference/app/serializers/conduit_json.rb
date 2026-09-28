class ConduitJson
  def initialize(viewer)
    @viewer = viewer
  end

  def user(user)
    { email: user.email, username: user.username, bio: user.bio, image: user.image, token: Token.issue(user) }
  end

  def profile(user)
    { username: user.username, bio: user.bio, image: user.image,
      following: !!@viewer&.outgoing_follows&.exists?(followed: user) }
  end

  def article(article, body: true)
    data = { slug: article.slug, title: article.title, description: article.description,
      tagList: article.tags, createdAt: article.created_at.iso8601(6), updatedAt: article.updated_at.iso8601(6),
      favorited: !!@viewer&.favorites&.exists?(article: article), favoritesCount: article.favorites.count,
      author: profile(article.author), status: article.status, publishedAt: article.published_at&.iso8601(6),
      revision: article.revision }
    data[:body] = article.body if body
    data
  end

  def comment(comment)
    { id: comment.id, createdAt: comment.created_at.iso8601(6), updatedAt: comment.updated_at.iso8601(6),
      body: comment.body, author: profile(comment.author) }
  end
end

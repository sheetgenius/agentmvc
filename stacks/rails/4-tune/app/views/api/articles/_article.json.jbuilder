json.extract! article, :slug, :title, :description
json.body article.body unless summary
json.tagList article.tags.map(&:name)
json.createdAt article.created_at
json.updatedAt article.updated_at
json.status article.status
json.publishedAt article.published_at
json.revision article.revision
json.favorited article.favorited_by?(current_user)
json.favoritesCount article.favorites.size
json.author do
  json.partial! "api/profiles/profile", user: article.author
end

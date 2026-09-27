json.extract! article, :slug, :title, :description
json.body article.body unless summary
json.tagList article.tags.pluck(:name)
json.createdAt article.created_at
json.updatedAt article.updated_at
json.favorited current_user ? current_user.favorites.exists?(article: article) : false
json.favoritesCount article.favorites.count
json.author do
  json.partial! "api/profiles/profile", user: article.author
end

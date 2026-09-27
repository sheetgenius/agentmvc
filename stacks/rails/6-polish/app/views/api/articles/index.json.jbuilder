json.articles @articles do |article|
  json.partial! "api/articles/article", article: article, summary: true
end
json.articlesCount @articles_count

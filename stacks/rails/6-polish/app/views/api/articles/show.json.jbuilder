json.article do
  json.partial! "api/articles/article", article: @article, summary: false
end

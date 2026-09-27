json.export do
  json.extract! @export, :id, :status
  json.createdAt @export.created_at
  json.completedAt @export.completed_at
  json.articles @export.articles
end

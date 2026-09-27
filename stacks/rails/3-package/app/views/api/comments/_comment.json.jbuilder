json.extract! comment, :id, :body
json.createdAt comment.created_at
json.updatedAt comment.updated_at
json.author do
  json.partial! "api/profiles/profile", user: comment.author
end

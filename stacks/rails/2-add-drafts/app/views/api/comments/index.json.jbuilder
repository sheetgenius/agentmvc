json.comments @comments do |comment|
  json.partial! "api/comments/comment", comment: comment
end

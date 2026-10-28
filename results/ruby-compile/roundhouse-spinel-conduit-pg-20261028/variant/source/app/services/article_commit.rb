class ArticleCommit
  def self.call(article, input, expected:, representation:, share: nil, key: nil)
    article.with_lock do
      raise ApplicationController::Failure.new(404, :share, "not found") if share && !(share.reload.valid_key?(key))
      if (input.key?("revision") || !expected.nil?) && !expected.is_a?(Integer)
        raise ApplicationController::Failure.new(422, :revision, "is invalid")
      end
      if expected && expected != article.revision
        raise ApplicationController::Failure.new(409, :revision, "is stale", article: representation.call(article))
      end
      # Roundhouse lacks Rails attribute string casting for the raw JSON values.
      changes = input.slice("title", "description", "body").transform_values { |value| JsonCast.string(value) }
      changes["slug"] = Article.slug_for(changes["title"]) if changes.key?("title") && changes["title"] != article.title
      if input.key?("tagList")
        tags = input["tagList"]
        raise ApplicationController::Failure.new(422, :tagList, "is invalid") unless tags.is_a?(Array) && tags.all? { |tag| tag.is_a?(String) }
        changes["tag_list"] = tags.uniq
      end
      # Generated update! consumes symbol attribute keys.
      article.update!(changes.merge("revision" => article.revision + 1).transform_keys { |name| name.to_sym })
    end
    LiveRooms.updated(article)
    article
  end
end

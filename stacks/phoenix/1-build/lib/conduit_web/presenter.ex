defmodule ConduitWeb.Presenter do
  alias Conduit.{Accounts, Content}

  def user(user) do
    %{
      email: user.email,
      username: user.username,
      bio: user.bio,
      image: user.image,
      token: Accounts.token(user)
    }
  end

  def profile(user, viewer) do
    %{
      username: user.username,
      bio: user.bio,
      image: user.image,
      following: Accounts.following?(viewer, user)
    }
  end

  def article(article, viewer, body? \\ true) do
    data = %{
      slug: article.slug,
      title: article.title,
      description: article.description,
      tagList: article.tag_list,
      createdAt: article.inserted_at,
      updatedAt: article.updated_at,
      favorited: Content.favorited?(viewer, article),
      favoritesCount: Content.favorites_count(article),
      author: profile(article.author, viewer)
    }

    if body?, do: Map.put(data, :body, article.body), else: data
  end

  def comment(comment, viewer) do
    %{
      id: comment.id,
      body: comment.body,
      createdAt: comment.inserted_at,
      updatedAt: comment.updated_at,
      author: profile(comment.author, viewer)
    }
  end
end

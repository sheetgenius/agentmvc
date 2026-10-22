class FavoritesController < ApplicationController
  def create
    require_user!
    article = public_article!
    Favorite.find_or_create_by!(article: article, user: @current_user)
    render json: { article: article_json(article) }
  end
  def destroy
    require_user!
    article = public_article!
    Favorite.where(article: article, user: @current_user).delete_all
    render json: { article: article_json(article) }
  end
end

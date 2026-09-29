package conduit

import (
	"context"

	"github.com/uptrace/bun"
)

func (a *App) userView(user *User) (UserView, error) {
	token, err := a.token(user)
	return UserView{Email: user.Email, Username: user.Username, Bio: user.Bio, Image: user.Image, Token: token}, err
}

func (a *App) profile(ctx context.Context, user *User, viewer *User) (Profile, error) {
	profiles, err := a.profiles(ctx, []User{*user}, viewer)
	return profiles[user.ID], err
}

func (a *App) profiles(ctx context.Context, users []User, viewer *User) (map[int64]Profile, error) {
	profiles := make(map[int64]Profile, len(users))
	ids := make([]int64, len(users))
	for i, user := range users {
		ids[i] = user.ID
		profiles[user.ID] = Profile{Username: user.Username, Bio: user.Bio, Image: user.Image}
	}
	if viewer == nil || len(users) == 0 {
		return profiles, nil
	}
	follows := make([]Follow, 0)
	if err := a.db.NewSelect().Model(&follows).Where("follower_id = ? AND followed_id IN (?)", viewer.ID, bun.In(ids)).Scan(ctx); err != nil {
		return nil, err
	}
	for _, follow := range follows {
		profile := profiles[follow.FollowedID]
		profile.Following = true
		profiles[follow.FollowedID] = profile
	}
	return profiles, nil
}

func (a *App) authorProfiles(ctx context.Context, ids []int64, viewer *User) (map[int64]Profile, error) {
	users := make([]User, 0)
	if err := a.db.NewSelect().Model(&users).Column("id", "username", "bio", "image").Where("id IN (?)", bun.In(ids)).Scan(ctx); err != nil {
		return nil, err
	}
	return a.profiles(ctx, users, viewer)
}

func articleFields(article *Article, full bool) ArticleView {
	view := ArticleView{
		Slug: article.Slug, Title: article.Title, Description: article.Description,
		Status: article.Status, PublishedAt: article.PublishedAt, Revision: article.Revision,
		CreatedAt: article.CreatedAt, UpdatedAt: article.UpdatedAt, TagList: []string{},
	}
	if full {
		view.Body = article.Body
	}
	return view
}

func (a *App) articleView(ctx context.Context, article *Article, viewer *User, full bool) (ArticleView, error) {
	views, err := a.articleViews(ctx, []Article{*article}, viewer, full)
	if err != nil {
		return ArticleView{}, err
	}
	return views[0], nil
}

func (a *App) articleViews(ctx context.Context, articles []Article, viewer *User, full bool) ([]ArticleView, error) {
	views := make([]ArticleView, len(articles))
	if len(articles) == 0 {
		return views, nil
	}
	articleIDs := make([]int64, len(articles))
	authorIDs := make([]int64, len(articles))
	for i, article := range articles {
		articleIDs[i] = article.ID
		authorIDs[i] = article.AuthorID
		views[i] = articleFields(&articles[i], full)
	}

	tags := make([]ArticleTag, 0)
	if err := a.db.NewSelect().Model(&tags).Where("article_id IN (?)", bun.In(articleIDs)).OrderExpr("article_id, position").Scan(ctx); err != nil {
		return nil, err
	}
	tagsByArticle := make(map[int64][]string, len(articles))
	for _, tag := range tags {
		tagsByArticle[tag.ArticleID] = append(tagsByArticle[tag.ArticleID], tag.Tag)
	}

	authors, err := a.authorProfiles(ctx, authorIDs, viewer)
	if err != nil {
		return nil, err
	}
	viewerID := int64(0)
	if viewer != nil {
		viewerID = viewer.ID
	}
	type favoriteSummary struct {
		ArticleID      int64
		FavoritesCount int
		Favorited      bool
	}
	var favorites []favoriteSummary
	if err := a.db.NewSelect().Table("favorites").Column("article_id").
		ColumnExpr("count(*) AS favorites_count").
		ColumnExpr("bool_or(user_id = ?) AS favorited", viewerID).
		Where("article_id IN (?)", bun.In(articleIDs)).Group("article_id").Scan(ctx, &favorites); err != nil {
		return nil, err
	}
	favoritesByArticle := make(map[int64]favoriteSummary, len(favorites))
	for _, favorite := range favorites {
		favoritesByArticle[favorite.ArticleID] = favorite
	}
	for i, article := range articles {
		views[i].Author = authors[article.AuthorID]
		if tags := tagsByArticle[article.ID]; tags != nil {
			views[i].TagList = tags
		}
		views[i].FavoritesCount = favoritesByArticle[article.ID].FavoritesCount
		views[i].Favorited = favoritesByArticle[article.ID].Favorited
	}
	return views, nil
}

func (a *App) commentView(ctx context.Context, comment *Comment, viewer *User) (CommentView, error) {
	views, err := a.commentViews(ctx, []Comment{*comment}, viewer)
	if err != nil {
		return CommentView{}, err
	}
	return views[0], nil
}

func (a *App) commentViews(ctx context.Context, comments []Comment, viewer *User) ([]CommentView, error) {
	views := make([]CommentView, len(comments))
	if len(comments) == 0 {
		return views, nil
	}
	authorIDs := make([]int64, len(comments))
	for i, comment := range comments {
		authorIDs[i] = comment.AuthorID
		views[i] = CommentView{ID: comment.ID, Body: comment.Body, CreatedAt: comment.CreatedAt, UpdatedAt: comment.UpdatedAt}
	}
	authors, err := a.authorProfiles(ctx, authorIDs, viewer)
	if err != nil {
		return nil, err
	}
	for i, comment := range comments {
		views[i].Author = authors[comment.AuthorID]
	}
	return views, nil
}

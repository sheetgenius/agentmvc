package conduit

import (
	"context"
	"time"

	"github.com/uptrace/bun"
)

type User struct {
	bun.BaseModel `bun:"table:users"`
	ID            int64  `bun:",pk,autoincrement"`
	Username      string `bun:",notnull"`
	Email         string `bun:",notnull"`
	PasswordHash  string `bun:",notnull"`
	Bio           *string
	Image         *string
}

type Article struct {
	bun.BaseModel `bun:"table:articles"`
	ID            int64 `bun:",pk,autoincrement"`
	AuthorID      int64
	Slug          string
	Title         string
	Description   string
	Body          string
	Status        string
	PublishedAt   *time.Time
	Revision      int
	CreatedAt     time.Time
	UpdatedAt     time.Time
}

type Comment struct {
	bun.BaseModel `bun:"table:comments"`
	ID            int64 `bun:",pk,autoincrement"`
	ArticleID     int64
	AuthorID      int64
	Body          string
	CreatedAt     time.Time
	UpdatedAt     time.Time
}

type Follow struct {
	bun.BaseModel `bun:"table:follows"`
	FollowerID    int64 `bun:",pk"`
	FollowedID    int64 `bun:",pk"`
}

type Favorite struct {
	bun.BaseModel `bun:"table:favorites"`
	UserID        int64 `bun:",pk"`
	ArticleID     int64 `bun:",pk"`
}

type ArticleTag struct {
	bun.BaseModel `bun:"table:article_tags"`
	ArticleID     int64  `bun:",pk"`
	Tag           string `bun:",pk"`
	Position      int
}

type Profile struct {
	Username  string  `json:"username"`
	Bio       *string `json:"bio"`
	Image     *string `json:"image"`
	Following bool    `json:"following"`
}

type ArticleView struct {
	Slug           string     `json:"slug"`
	Title          string     `json:"title"`
	Description    string     `json:"description"`
	Body           string     `json:"body,omitempty"`
	Status         string     `json:"status"`
	PublishedAt    *time.Time `json:"publishedAt"`
	Revision       int        `json:"revision"`
	TagList        []string   `json:"tagList"`
	CreatedAt      time.Time  `json:"createdAt"`
	UpdatedAt      time.Time  `json:"updatedAt"`
	Favorited      bool       `json:"favorited"`
	FavoritesCount int        `json:"favoritesCount"`
	Author         Profile    `json:"author"`
}

type CommentView struct {
	ID        int64     `json:"id"`
	CreatedAt time.Time `json:"createdAt"`
	UpdatedAt time.Time `json:"updatedAt"`
	Body      string    `json:"body"`
	Author    Profile   `json:"author"`
}

func (a *App) userByID(ctx context.Context, id int64) (*User, error) {
	u := new(User)
	err := a.db.NewSelect().Model(u).Where("id = ?", id).Scan(ctx)
	return u, err
}

func (a *App) userByName(ctx context.Context, name string) (*User, error) {
	u := new(User)
	err := a.db.NewSelect().Model(u).Where("username = ?", name).Scan(ctx)
	return u, err
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
	if viewer != nil {
		follows := make([]Follow, 0)
		if err := a.db.NewSelect().Model(&follows).Where("follower_id = ? AND followed_id IN (?)", viewer.ID, bun.In(ids)).Scan(ctx); err != nil {
			return nil, err
		}
		for _, follow := range follows {
			profile := profiles[follow.FollowedID]
			profile.Following = true
			profiles[follow.FollowedID] = profile
		}
	}
	return profiles, nil
}

func (a *App) articleView(ctx context.Context, article *Article, viewer *User, full bool) (ArticleView, error) {
	views, err := a.articleViews(ctx, []Article{*article}, viewer, full)
	if err != nil {
		return ArticleView{}, err
	}
	return views[0], nil
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

	users := make([]User, 0)
	if err := a.db.NewSelect().Model(&users).Column("id", "username", "bio", "image").Where("id IN (?)", bun.In(authorIDs)).Scan(ctx); err != nil {
		return nil, err
	}
	viewerID := int64(0)
	if viewer != nil {
		viewerID = viewer.ID
	}
	authors, err := a.profiles(ctx, users, viewer)
	if err != nil {
		return nil, err
	}

	var favorites []struct {
		ArticleID      int64
		FavoritesCount int
		Favorited      bool
	}
	if err := a.db.NewSelect().Table("favorites").Column("article_id").
		ColumnExpr("count(*) AS favorites_count").
		ColumnExpr("bool_or(user_id = ?) AS favorited", viewerID).
		Where("article_id IN (?)", bun.In(articleIDs)).Group("article_id").Scan(ctx, &favorites); err != nil {
		return nil, err
	}
	favoritesByArticle := make(map[int64]int, len(favorites))
	favoritedByViewer := make(map[int64]bool, len(favorites))
	for _, favorite := range favorites {
		favoritesByArticle[favorite.ArticleID] = favorite.FavoritesCount
		favoritedByViewer[favorite.ArticleID] = favorite.Favorited
	}
	for i, article := range articles {
		views[i].Author = authors[article.AuthorID]
		if tags := tagsByArticle[article.ID]; tags != nil {
			views[i].TagList = tags
		}
		views[i].FavoritesCount = favoritesByArticle[article.ID]
		views[i].Favorited = favoritedByViewer[article.ID]
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
	users := make([]User, 0)
	if err := a.db.NewSelect().Model(&users).Column("id", "username", "bio", "image").Where("id IN (?)", bun.In(authorIDs)).Scan(ctx); err != nil {
		return nil, err
	}
	authors, err := a.profiles(ctx, users, viewer)
	if err != nil {
		return nil, err
	}
	for i, comment := range comments {
		views[i].Author = authors[comment.AuthorID]
	}
	return views, nil
}

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
	Slug           string    `json:"slug"`
	Title          string    `json:"title"`
	Description    string    `json:"description"`
	Body           string    `json:"body,omitempty"`
	TagList        []string  `json:"tagList"`
	CreatedAt      time.Time `json:"createdAt"`
	UpdatedAt      time.Time `json:"updatedAt"`
	Favorited      bool      `json:"favorited"`
	FavoritesCount int       `json:"favoritesCount"`
	Author         Profile   `json:"author"`
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

func (a *App) articleBySlug(ctx context.Context, slug string) (*Article, error) {
	article := new(Article)
	err := a.db.NewSelect().Model(article).Where("slug = ?", slug).Scan(ctx)
	return article, err
}

func (a *App) profile(ctx context.Context, user *User, viewer *User) (Profile, error) {
	p := Profile{Username: user.Username, Bio: user.Bio, Image: user.Image}
	if viewer != nil {
		var err error
		p.Following, err = a.db.NewSelect().Table("follows").Where("follower_id = ? AND followed_id = ?", viewer.ID, user.ID).Exists(ctx)
		if err != nil {
			return p, err
		}
	}
	return p, nil
}

func (a *App) articleView(ctx context.Context, article *Article, viewer *User, full bool) (ArticleView, error) {
	v := ArticleView{
		Slug: article.Slug, Title: article.Title, Description: article.Description,
		CreatedAt: article.CreatedAt, UpdatedAt: article.UpdatedAt, TagList: []string{},
	}
	if full {
		v.Body = article.Body
	}
	if err := a.db.NewSelect().Table("article_tags").Column("tag").Where("article_id = ?", article.ID).Order("position").Scan(ctx, &v.TagList); err != nil {
		return v, err
	}
	author, err := a.userByID(ctx, article.AuthorID)
	if err != nil {
		return v, err
	}
	v.Author, err = a.profile(ctx, author, viewer)
	if err != nil {
		return v, err
	}
	v.FavoritesCount, err = a.db.NewSelect().Table("favorites").Where("article_id = ?", article.ID).Count(ctx)
	if err != nil {
		return v, err
	}
	if viewer != nil {
		v.Favorited, err = a.db.NewSelect().Table("favorites").Where("article_id = ? AND user_id = ?", article.ID, viewer.ID).Exists(ctx)
	}
	return v, err
}

func (a *App) commentView(ctx context.Context, comment *Comment, viewer *User) (CommentView, error) {
	v := CommentView{ID: comment.ID, Body: comment.Body, CreatedAt: comment.CreatedAt, UpdatedAt: comment.UpdatedAt}
	author, err := a.userByID(ctx, comment.AuthorID)
	if err != nil {
		return v, err
	}
	v.Author, err = a.profile(ctx, author, viewer)
	return v, err
}

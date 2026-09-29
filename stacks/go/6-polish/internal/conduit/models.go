package conduit

import (
	"time"

	"github.com/uptrace/bun"
)

type User struct {
	bun.BaseModel       `bun:"table:users"`
	ID                  int64  `bun:",pk,autoincrement"`
	Username            string `bun:",notnull"`
	Email               string `bun:",notnull"`
	PasswordHash        string `bun:",notnull"`
	Bio                 *string
	Image               *string
	FailedLoginAttempts int
	LastFailedLoginAt   *time.Time
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

type UserView struct {
	Email    string  `json:"email"`
	Username string  `json:"username"`
	Bio      *string `json:"bio"`
	Image    *string `json:"image"`
	Token    string  `json:"token"`
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

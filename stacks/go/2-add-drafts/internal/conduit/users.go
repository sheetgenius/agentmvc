package conduit

import (
	"crypto/sha256"
	"database/sql"
	"encoding/hex"
	"errors"
	"net/http"
	"strings"
	"unicode/utf8"

	"github.com/go-chi/chi/v5"
	"github.com/jackc/pgx/v5/pgconn"
	"golang.org/x/crypto/bcrypt"
)

func (a *App) userResponse(user *User) (map[string]any, error) {
	token, err := a.token(user)
	return map[string]any{"email": user.Email, "username": user.Username, "bio": user.Bio, "image": user.Image, "token": token}, err
}

func (a *App) sendUser(w http.ResponseWriter, status int, user *User) error {
	response, err := a.userResponse(user)
	if err == nil {
		write(w, status, map[string]any{"user": response})
	}
	return err
}

func userConflict(err error) error {
	var pg *pgconn.PgError
	if !errors.As(err, &pg) || pg.Code != "23505" {
		return err
	}
	field := "username"
	if strings.Contains(pg.ConstraintName, "email") {
		field = "email"
	}
	return apiError{status: http.StatusConflict, field: field, text: "has already been taken"}
}

// Bcrypt's 72-byte limit would reject long multibyte passwords.
func passwordDigest(password string) []byte {
	sum := sha256.Sum256([]byte(password))
	return []byte(hex.EncodeToString(sum[:]))
}

func passwordHash(password string) (string, error) {
	if utf8.RuneCountInString(password) < 8 {
		return "", apiError{status: http.StatusUnprocessableEntity, field: "password", text: "is too short"}
	}
	hash, err := bcrypt.GenerateFromPassword(passwordDigest(password), bcrypt.DefaultCost)
	return string(hash), err
}

func (a *App) register(w http.ResponseWriter, r *http.Request) error {
	fields, err := decodeObject(r, "user")
	if err != nil {
		return err
	}
	username, err := requiredString(fields, "username")
	if err != nil {
		return err
	}
	email, err := requiredString(fields, "email")
	if err != nil {
		return err
	}
	password, err := requiredString(fields, "password")
	if err != nil {
		return err
	}
	hash, err := passwordHash(password)
	if err != nil {
		return err
	}
	user := &User{Username: username, Email: email, PasswordHash: hash}
	if _, err := a.db.NewInsert().Model(user).Exec(r.Context()); err != nil {
		return userConflict(err)
	}
	return a.sendUser(w, http.StatusCreated, user)
}

func (a *App) login(w http.ResponseWriter, r *http.Request) error {
	fields, err := decodeObject(r, "user")
	if err != nil {
		return err
	}
	email, err := requiredString(fields, "email")
	if err != nil {
		return err
	}
	password, err := requiredString(fields, "password")
	if err != nil {
		return err
	}
	user := new(User)
	err = a.db.NewSelect().Model(user).Where("email = ?", email).Scan(r.Context())
	if errors.Is(err, sql.ErrNoRows) || err == nil && bcrypt.CompareHashAndPassword([]byte(user.PasswordHash), passwordDigest(password)) != nil {
		return apiError{status: http.StatusUnauthorized, field: "credentials", text: "invalid"}
	}
	if err != nil {
		return err
	}
	return a.sendUser(w, http.StatusOK, user)
}

func (a *App) currentUser(w http.ResponseWriter, r *http.Request) error {
	return a.sendUser(w, http.StatusOK, viewer(r))
}

func (a *App) updateUser(w http.ResponseWriter, r *http.Request) error {
	fields, err := decodeObject(r, "user")
	if err != nil {
		return err
	}
	user := viewer(r)
	if value, ok, err := stringField(fields, "username"); err != nil {
		return err
	} else if ok {
		user.Username = value
	}
	if value, ok, err := stringField(fields, "email"); err != nil {
		return err
	} else if ok {
		user.Email = value
	}
	if value, ok, err := stringField(fields, "password"); err != nil {
		return err
	} else if ok {
		hash, err := passwordHash(value)
		if err != nil {
			return err
		}
		user.PasswordHash = hash
	}
	if err := nullableString(fields, "bio", &user.Bio); err != nil {
		return err
	}
	if err := nullableString(fields, "image", &user.Image); err != nil {
		return err
	}
	if _, err := a.db.NewUpdate().Model(user).Column("username", "email", "password_hash", "bio", "image").WherePK().Exec(r.Context()); err != nil {
		return userConflict(err)
	}
	return a.sendUser(w, http.StatusOK, user)
}

func (a *App) getProfile(w http.ResponseWriter, r *http.Request) error {
	user, err := a.userByName(r.Context(), chi.URLParam(r, "username"))
	if errors.Is(err, sql.ErrNoRows) {
		return missing("profile")
	}
	if err != nil {
		return err
	}
	profile, err := a.profile(r.Context(), user, viewer(r))
	if err == nil {
		write(w, http.StatusOK, map[string]any{"profile": profile})
	}
	return err
}

func (a *App) setFollow(w http.ResponseWriter, r *http.Request) error {
	user, err := a.userByName(r.Context(), chi.URLParam(r, "username"))
	if errors.Is(err, sql.ErrNoRows) {
		return missing("profile")
	}
	if err != nil {
		return err
	}
	if r.Method == http.MethodPost {
		_, err = a.db.NewInsert().Model(&Follow{FollowerID: viewer(r).ID, FollowedID: user.ID}).On("CONFLICT DO NOTHING").Exec(r.Context())
	} else {
		_, err = a.db.NewDelete().Table("follows").Where("follower_id = ? AND followed_id = ?", viewer(r).ID, user.ID).Exec(r.Context())
	}
	if err != nil {
		return err
	}
	profile, err := a.profile(r.Context(), user, viewer(r))
	if err == nil {
		write(w, http.StatusOK, map[string]any{"profile": profile})
	}
	return err
}

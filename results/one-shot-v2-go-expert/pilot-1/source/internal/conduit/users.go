package conduit

import (
	"database/sql"
	"errors"
	"net/http"
	"strings"

	"github.com/go-chi/chi/v5"
	"github.com/jackc/pgx/v5/pgconn"
	"golang.org/x/crypto/bcrypt"
)

type userRow struct {
	ID                    int64
	Username, Email, Hash string
	Bio, Image            sql.NullString
}

func scanUser(row *sql.Row) (userRow, error) {
	var u userRow
	err := row.Scan(&u.ID, &u.Username, &u.Email, &u.Hash, &u.Bio, &u.Image)
	return u, err
}
func (a *App) userByID(id int64) (userRow, error) {
	return scanUser(a.DB.DB.QueryRow("SELECT id,username,email,password_hash,bio,image FROM users WHERE id=$1", id))
}
func (a *App) userResponse(u userRow) any {
	return map[string]any{"user": map[string]any{"email": u.Email, "token": a.token(u.ID), "username": u.Username, "bio": nullable(u.Bio), "image": nullable(u.Image)}}
}
func nullable(v sql.NullString) any {
	if !v.Valid {
		return nil
	}
	return v.String
}
func uniqueError(err error) error {
	var e *pgconn.PgError
	if errors.As(err, &e) && e.Code == "23505" {
		if strings.Contains(e.ConstraintName, "username") {
			return fail(409, "username", "has already been taken")
		}
		if strings.Contains(e.ConstraintName, "email") {
			return fail(409, "email", "has already been taken")
		}
	}
	return err
}
func (a *App) register(w http.ResponseWriter, r *http.Request) error {
	obj, err := decode(r, "user")
	if err != nil {
		return err
	}
	username, err := required(obj, "username")
	if err != nil {
		return err
	}
	email, err := required(obj, "email")
	if err != nil {
		return err
	}
	password, err := required(obj, "password")
	if err != nil {
		return err
	}
	if len(password) < 8 {
		return fail(422, "password", "is too short")
	}
	hash, err := bcrypt.GenerateFromPassword([]byte(password), bcrypt.DefaultCost)
	if err != nil {
		return err
	}
	var id int64
	err = a.DB.DB.QueryRowContext(r.Context(), "INSERT INTO users(username,email,password_hash) VALUES($1,$2,$3) RETURNING id", username, email, string(hash)).Scan(&id)
	if err != nil {
		return uniqueError(err)
	}
	u, err := a.userByID(id)
	if err != nil {
		return err
	}
	send(w, 201, a.userResponse(u))
	return nil
}
func (a *App) login(w http.ResponseWriter, r *http.Request) error {
	obj, err := decode(r, "user")
	if err != nil {
		return err
	}
	email, err := required(obj, "email")
	if err != nil {
		return err
	}
	password, err := required(obj, "password")
	if err != nil {
		return err
	}
	a.loginMu.Lock()
	count := a.failures[email]
	a.loginMu.Unlock()
	if count >= 20 {
		return fail(429, "credentials", "rate limited")
	}
	u, err := scanUser(a.DB.DB.QueryRowContext(r.Context(), "SELECT id,username,email,password_hash,bio,image FROM users WHERE email=$1", email))
	valid := err == nil && bcrypt.CompareHashAndPassword([]byte(u.Hash), []byte(password)) == nil
	if !valid {
		a.loginMu.Lock()
		a.failures[email]++
		a.loginMu.Unlock()
		return fail(401, "credentials", "invalid")
	}
	a.loginMu.Lock()
	delete(a.failures, email)
	a.loginMu.Unlock()
	send(w, 200, a.userResponse(u))
	return nil
}
func (a *App) currentUser(w http.ResponseWriter, r *http.Request) error {
	id, err := a.caller(r, true)
	if err != nil {
		return err
	}
	u, err := a.userByID(id)
	if err != nil {
		return err
	}
	send(w, 200, a.userResponse(u))
	return nil
}
func (a *App) updateUser(w http.ResponseWriter, r *http.Request) error {
	id, err := a.caller(r, true)
	if err != nil {
		return err
	}
	obj, err := decode(r, "user")
	if err != nil {
		return err
	}
	u, err := a.userByID(id)
	if err != nil {
		return err
	}
	for _, key := range []string{"username", "email", "password"} {
		if _, ok := obj[key]; !ok {
			continue
		}
		v, e := required(obj, key)
		if e != nil {
			return e
		}
		if key == "password" {
			if len(v) < 8 {
				return fail(422, "password", "is too short")
			}
			hash, e := bcrypt.GenerateFromPassword([]byte(v), bcrypt.DefaultCost)
			if e != nil {
				return e
			}
			u.Hash = string(hash)
		} else if key == "username" {
			u.Username = v
		} else {
			u.Email = v
		}
	}
	for _, key := range []string{"bio", "image"} {
		if _, ok := obj[key]; !ok {
			continue
		}
		var v *string
		if string(obj[key]) != "null" {
			s, _, e := field(obj, key)
			if e != nil {
				return e
			}
			if s != "" {
				v = &s
			}
		}
		n := sql.NullString{}
		if v != nil {
			n = sql.NullString{String: *v, Valid: true}
		}
		if key == "bio" {
			u.Bio = n
		} else {
			u.Image = n
		}
	}
	_, err = a.DB.DB.ExecContext(r.Context(), "UPDATE users SET username=$1,email=$2,password_hash=$3,bio=$4,image=$5 WHERE id=$6", u.Username, u.Email, u.Hash, u.Bio, u.Image, id)
	if err != nil {
		return uniqueError(err)
	}
	send(w, 200, a.userResponse(u))
	return nil
}

type profileView struct {
	Username  string `json:"username"`
	Bio       any    `json:"bio"`
	Image     any    `json:"image"`
	Following bool   `json:"following"`
}

func (a *App) profileByName(r *http.Request, name string, viewer int64) (int64, profileView, error) {
	var id int64
	var bio, image sql.NullString
	var following bool
	err := a.DB.DB.QueryRowContext(r.Context(), `SELECT u.id,u.bio,u.image,EXISTS(SELECT 1 FROM follows f WHERE f.follower_id=$2 AND f.followed_id=u.id) FROM users u WHERE username=$1`, name, viewer).Scan(&id, &bio, &image, &following)
	if errors.Is(err, sql.ErrNoRows) {
		return 0, profileView{}, fail(404, "profile", "not found")
	}
	if err != nil {
		return 0, profileView{}, err
	}
	return id, profileView{name, nullable(bio), nullable(image), following}, nil
}
func (a *App) profile(w http.ResponseWriter, r *http.Request) error {
	viewer, err := a.caller(r, false)
	if err != nil {
		return err
	}
	_, p, err := a.profileByName(r, chi.URLParam(r, "username"), viewer)
	if err != nil {
		return err
	}
	send(w, 200, map[string]any{"profile": p})
	return nil
}
func (a *App) follow(w http.ResponseWriter, r *http.Request) error {
	viewer, err := a.caller(r, true)
	if err != nil {
		return err
	}
	target, p, err := a.profileByName(r, chi.URLParam(r, "username"), viewer)
	if err != nil {
		return err
	}
	if target == viewer {
		return fail(422, "profile", "cannot follow yourself")
	}
	if r.Method == "POST" {
		_, err = a.DB.DB.ExecContext(r.Context(), "INSERT INTO follows(follower_id,followed_id) VALUES($1,$2) ON CONFLICT DO NOTHING", viewer, target)
		p.Following = true
	} else {
		_, err = a.DB.DB.ExecContext(r.Context(), "DELETE FROM follows WHERE follower_id=$1 AND followed_id=$2", viewer, target)
		p.Following = false
	}
	if err != nil {
		return err
	}
	send(w, 200, map[string]any{"profile": p})
	return nil
}

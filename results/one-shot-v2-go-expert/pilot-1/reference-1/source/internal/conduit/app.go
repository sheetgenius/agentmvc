package conduit

import (
	"crypto/rand"
	"database/sql"
	"encoding/base64"
	"encoding/json"
	"errors"
	"io"
	"log/slog"
	"net/http"
	"strconv"
	"strings"
	"time"

	"github.com/go-chi/chi/v5"
	"github.com/golang-jwt/jwt/v5"
	"github.com/riverqueue/river"
	"github.com/uptrace/bun"
)

type App struct {
	DB     *bun.DB
	Secret []byte
	Jobs   *river.Client[*sql.Tx]
	rooms  *rooms
	logins loginLimiter
}

func New(db *bun.DB, secret string) *App {
	return &App{DB: db, Secret: []byte(secret), rooms: newRooms()}
}

type failure struct {
	Status         int
	Field, Message string
	Article        any
}

func (e failure) Error() string { return e.Field + ": " + e.Message }
func fail(status int, field, message string) error {
	return failure{Status: status, Field: field, Message: message}
}
func bad(field string) error { return fail(422, field, "can't be blank") }

func send(w http.ResponseWriter, status int, value any) {
	w.Header().Set("Content-Type", "application/json; charset=utf-8")
	w.Header().Set("X-Content-Type-Options", "nosniff")
	w.WriteHeader(status)
	if value != nil {
		_ = json.NewEncoder(w).Encode(value)
	}
}
func sendError(w http.ResponseWriter, err error) {
	var f failure
	if errors.As(err, &f) {
		body := map[string]any{"errors": map[string][]string{f.Field: {f.Message}}}
		if f.Article != nil {
			body["article"] = f.Article
		}
		send(w, f.Status, body)
		return
	}
	slog.Error("request failed", "error", err)
	send(w, 500, map[string]any{"errors": map[string][]string{"server": {"internal error"}}})
}

type handler func(http.ResponseWriter, *http.Request) error

func (a *App) route(r chi.Router, method, path string, h handler) {
	r.MethodFunc(method, path, func(w http.ResponseWriter, req *http.Request) {
		if err := h(w, req); err != nil {
			sendError(w, err)
		}
	})
}
func decode(req *http.Request, key string) (map[string]json.RawMessage, error) {
	return decodeBody(req, key, false)
}
func decodeShared(req *http.Request) (map[string]json.RawMessage, error) {
	return decodeBody(req, "article", true)
}
func decodeBody(req *http.Request, key string, strict bool) (map[string]json.RawMessage, error) {
	req.Body = http.MaxBytesReader(nil, req.Body, 4<<20)
	var root map[string]json.RawMessage
	decoder := json.NewDecoder(req.Body)
	if err := decoder.Decode(&root); err != nil {
		return nil, fail(422, "body", "is invalid")
	}
	if strict {
		var extra any
		if len(root) != 1 || decoder.Decode(&extra) != io.EOF {
			return nil, fail(422, "body", "is invalid")
		}
	}
	var obj map[string]json.RawMessage
	if err := json.Unmarshal(root[key], &obj); err != nil || obj == nil {
		return nil, fail(422, key, "is invalid")
	}
	return obj, nil
}
func field(obj map[string]json.RawMessage, key string) (string, bool, error) {
	raw, ok := obj[key]
	if !ok {
		return "", false, nil
	}
	var v string
	if err := json.Unmarshal(raw, &v); err != nil {
		return "", true, fail(422, key, "is invalid")
	}
	return v, true, nil
}
func required(obj map[string]json.RawMessage, key string) (string, error) {
	v, _, err := field(obj, key)
	if err != nil {
		return "", err
	}
	if strings.TrimSpace(v) == "" {
		return "", bad(key)
	}
	return v, nil
}
func integer(obj map[string]json.RawMessage, key string) (int, bool, error) {
	raw, ok := obj[key]
	if !ok {
		return 0, false, nil
	}
	var v *int
	if err := json.Unmarshal(raw, &v); err != nil || v == nil {
		return 0, true, fail(422, key, "is invalid")
	}
	return *v, true, nil
}
func randomURL(n int) string {
	b := make([]byte, n)
	_, _ = rand.Read(b)
	return base64.RawURLEncoding.EncodeToString(b)
}
func (a *App) token(id int64) string {
	t := jwt.NewWithClaims(jwt.SigningMethodHS256, jwt.RegisteredClaims{Subject: strconv.FormatInt(id, 10), ExpiresAt: jwt.NewNumericDate(time.Now().Add(30 * 24 * time.Hour))})
	s, _ := t.SignedString(a.Secret)
	return s
}
func (a *App) caller(req *http.Request, required bool) (int64, error) {
	auth := req.Header.Get("Authorization")
	if auth == "" {
		if required {
			return 0, fail(401, "token", "is missing")
		}
		return 0, nil
	}
	if !strings.HasPrefix(auth, "Token ") {
		return 0, fail(401, "token", "is invalid")
	}
	t, err := jwt.Parse(strings.TrimPrefix(auth, "Token "), func(t *jwt.Token) (any, error) {
		if t.Method.Alg() != "HS256" {
			return nil, errors.New("algorithm")
		}
		return a.Secret, nil
	}, jwt.WithValidMethods([]string{"HS256"}))
	if err != nil || !t.Valid {
		return 0, fail(401, "token", "is invalid")
	}
	sub, ok := t.Claims.(jwt.MapClaims)["sub"].(string)
	if !ok {
		return 0, fail(401, "token", "is invalid")
	}
	id, err := strconv.ParseInt(sub, 10, 64)
	if err != nil {
		return 0, fail(401, "token", "is invalid")
	}
	var exists bool
	if err = a.DB.DB.QueryRowContext(req.Context(), "SELECT EXISTS(SELECT 1 FROM users WHERE id=$1)", id).Scan(&exists); err != nil {
		return 0, err
	}
	if !exists {
		return 0, fail(401, "token", "is invalid")
	}
	return id, nil
}
func (a *App) Routes(r chi.Router) {
	a.route(r, "POST", "/api/users", a.register)
	a.route(r, "POST", "/api/users/login", a.login)
	a.route(r, "GET", "/api/user", a.currentUser)
	a.route(r, "PUT", "/api/user", a.updateUser)
	a.route(r, "GET", "/api/profiles/{username}", a.profile)
	a.route(r, "POST", "/api/profiles/{username}/follow", a.follow)
	a.route(r, "DELETE", "/api/profiles/{username}/follow", a.follow)
	a.route(r, "GET", "/api/articles", a.listArticles)
	a.route(r, "GET", "/api/articles/feed", a.listArticles)
	a.route(r, "GET", "/api/user/drafts", a.listArticles)
	a.route(r, "POST", "/api/articles", a.createArticle)
	a.route(r, "GET", "/api/articles/{slug}", a.getArticle)
	a.route(r, "PUT", "/api/articles/{slug}", a.updateArticle)
	a.route(r, "DELETE", "/api/articles/{slug}", a.deleteArticle)
	a.route(r, "POST", "/api/articles/{slug}/publish", a.publishArticle)
	a.route(r, "POST", "/api/articles/{slug}/favorite", a.favorite)
	a.route(r, "DELETE", "/api/articles/{slug}/favorite", a.favorite)
	a.route(r, "GET", "/api/articles/{slug}/comments", a.comments)
	a.route(r, "POST", "/api/articles/{slug}/comments", a.comments)
	a.route(r, "DELETE", "/api/articles/{slug}/comments/{id}", a.deleteComment)
	a.route(r, "POST", "/api/articles/{slug}/share", a.share)
	a.route(r, "DELETE", "/api/articles/{slug}/share", a.share)
	a.route(r, "GET", "/api/shares/{id}/article", a.sharedArticle)
	a.route(r, "PUT", "/api/shares/{id}/article", a.sharedArticle)
	r.Get("/api/shares/{id}/live", a.live)
	a.route(r, "POST", "/api/user/exports", a.createExport)
	a.route(r, "GET", "/api/user/exports/{id}", a.getExport)
}

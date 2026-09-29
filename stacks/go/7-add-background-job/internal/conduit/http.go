package conduit

import (
	"context"
	"database/sql"
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
	db     *bun.DB
	jobs   *river.Client[*sql.Tx]
	secret []byte
}

type viewerKey struct{}

type endpoint func(http.ResponseWriter, *http.Request) error

type apiError struct {
	status  int
	field   string
	text    string
	article *ArticleView
}

func (e apiError) Error() string { return e.field + ": " + e.text }

func invalid(field string) error {
	return apiError{status: http.StatusUnprocessableEntity, field: field, text: "can't be blank"}
}
func missing(field string) error {
	return apiError{status: http.StatusNotFound, field: field, text: "not found"}
}
func forbidden(field string) error {
	return apiError{status: http.StatusForbidden, field: field, text: "forbidden"}
}

func New(db *bun.DB, jobs *river.Client[*sql.Tx], secret string) http.Handler {
	a := &App{db: db, jobs: jobs, secret: []byte(secret)}
	r := chi.NewRouter()
	r.Use(func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.Header().Set("X-Content-Type-Options", "nosniff")
			w.Header().Set("Access-Control-Allow-Origin", "*")
			w.Header().Set("Access-Control-Allow-Headers", "Authorization, Content-Type")
			w.Header().Set("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
			if r.Method == http.MethodOptions {
				w.WriteHeader(http.StatusNoContent)
				return
			}
			next.ServeHTTP(w, r)
		})
	})
	r.Route("/api", func(r chi.Router) {
		a.route(r, "POST", "/users", false, a.register)
		a.route(r, "POST", "/users/login", false, a.login)
		a.route(r, "GET", "/user", true, a.currentUser)
		a.route(r, "PUT", "/user", true, a.updateUser)
		a.route(r, "GET", "/user/drafts", true, a.drafts)
		a.route(r, "POST", "/user/exports", true, a.createExport)
		a.route(r, "GET", "/user/exports/{id}", true, a.getExport)
		a.route(r, "GET", "/profiles/{username}", false, a.getProfile)
		a.route(r, "POST", "/profiles/{username}/follow", true, a.setFollow)
		a.route(r, "DELETE", "/profiles/{username}/follow", true, a.setFollow)
		a.route(r, "GET", "/articles", false, a.listArticles)
		a.route(r, "GET", "/articles/feed", true, a.feed)
		a.route(r, "POST", "/articles", true, a.createArticle)
		a.route(r, "GET", "/articles/{slug}", false, a.getArticle)
		a.route(r, "PUT", "/articles/{slug}", true, a.updateArticle)
		a.route(r, "DELETE", "/articles/{slug}", true, a.deleteArticle)
		a.route(r, "POST", "/articles/{slug}/publish", true, a.publishArticle)
		a.route(r, "POST", "/articles/{slug}/favorite", true, a.setFavorite)
		a.route(r, "DELETE", "/articles/{slug}/favorite", true, a.setFavorite)
		a.route(r, "GET", "/articles/{slug}/comments", false, a.listComments)
		a.route(r, "POST", "/articles/{slug}/comments", true, a.createComment)
		a.route(r, "DELETE", "/articles/{slug}/comments/{id}", true, a.deleteComment)
		a.route(r, "GET", "/tags", false, a.tags)
	})
	return r
}

func (a *App) route(r chi.Router, method, path string, required bool, fn endpoint) {
	r.MethodFunc(method, path, func(w http.ResponseWriter, r *http.Request) {
		viewer, err := a.authenticate(r)
		if err == nil && required && viewer == nil {
			err = apiError{status: http.StatusUnauthorized, field: "token", text: "is missing"}
		}
		if err == nil {
			err = fn(w, r.WithContext(context.WithValue(r.Context(), viewerKey{}, viewer)))
		}
		if err != nil {
			var api apiError
			if !errors.As(err, &api) {
				slog.Error("request failed", "method", r.Method, "path", r.URL.Path, "error", err)
				api = apiError{status: http.StatusInternalServerError, field: "body", text: "internal error"}
			}
			body := map[string]any{"errors": map[string][]string{api.field: {api.text}}}
			if api.article != nil {
				body["article"] = api.article
			}
			write(w, api.status, body)
		}
	})
}

func (a *App) authenticate(r *http.Request) (*User, error) {
	header := r.Header.Get("Authorization")
	if header == "" {
		return nil, nil
	}
	if !strings.HasPrefix(header, "Token ") {
		return nil, apiError{status: http.StatusUnauthorized, field: "token", text: "is invalid"}
	}
	claims := new(jwt.RegisteredClaims)
	_, err := jwt.ParseWithClaims(strings.TrimPrefix(header, "Token "), claims, func(t *jwt.Token) (any, error) {
		if t.Method.Alg() != jwt.SigningMethodHS256.Alg() {
			return nil, errors.New("unexpected signing method")
		}
		return a.secret, nil
	})
	if err != nil {
		return nil, apiError{status: http.StatusUnauthorized, field: "token", text: "is invalid"}
	}
	id, err := strconv.ParseInt(claims.Subject, 10, 64)
	if err != nil {
		return nil, apiError{status: http.StatusUnauthorized, field: "token", text: "is invalid"}
	}
	user, err := a.userByID(r.Context(), id)
	if errors.Is(err, sql.ErrNoRows) {
		return nil, apiError{status: http.StatusUnauthorized, field: "token", text: "is invalid"}
	}
	return user, err
}

func viewer(r *http.Request) *User {
	user, _ := r.Context().Value(viewerKey{}).(*User)
	return user
}

func (a *App) token(user *User) (string, error) {
	claims := jwt.RegisteredClaims{Subject: strconv.FormatInt(user.ID, 10), ExpiresAt: jwt.NewNumericDate(time.Now().Add(30 * 24 * time.Hour))}
	return jwt.NewWithClaims(jwt.SigningMethodHS256, claims).SignedString(a.secret)
}

func write(w http.ResponseWriter, status int, body any) {
	if body != nil {
		w.Header().Set("Content-Type", "application/json; charset=utf-8")
	}
	w.WriteHeader(status)
	if body != nil {
		_ = json.NewEncoder(w).Encode(body)
	}
}

func decodeObject(r *http.Request, name string) (map[string]json.RawMessage, error) {
	var envelope map[string]json.RawMessage
	if err := json.NewDecoder(io.LimitReader(r.Body, 1<<20)).Decode(&envelope); err != nil {
		return nil, apiError{status: http.StatusUnprocessableEntity, field: "body", text: "can't be empty"}
	}
	var fields map[string]json.RawMessage
	if err := json.Unmarshal(envelope[name], &fields); err != nil || fields == nil {
		return nil, apiError{status: http.StatusUnprocessableEntity, field: "body", text: "can't be empty"}
	}
	return fields, nil
}

func stringField(fields map[string]json.RawMessage, name string) (string, bool, error) {
	raw, present := fields[name]
	if !present {
		return "", false, nil
	}
	var value string
	if err := json.Unmarshal(raw, &value); err != nil || strings.TrimSpace(value) == "" {
		return "", true, invalid(name)
	}
	return value, true, nil
}

func requiredString(fields map[string]json.RawMessage, name string) (string, error) {
	value, _, err := stringField(fields, name)
	if err != nil || value == "" {
		return "", invalid(name)
	}
	return value, nil
}

func nullableString(fields map[string]json.RawMessage, name string, value **string) error {
	raw, ok := fields[name]
	if !ok {
		return nil
	}
	var s *string
	if err := json.Unmarshal(raw, &s); err != nil {
		return invalid(name)
	}
	if s != nil && *s == "" {
		*value = nil
	} else {
		*value = s
	}
	return nil
}

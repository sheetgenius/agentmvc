package conduit

import (
	"context"
	"encoding/json"
	"net/http/httptest"
	"os"
	"sync"
	"testing"

	"conduit/internal/platform"
	"github.com/go-chi/chi/v5"
)

func TestDraftVisibilityRevisionAndPublish(t *testing.T) {
	url := os.Getenv("DATABASE_URL")
	if url == "" {
		t.Skip("DATABASE_URL is required for database transition test")
	}
	ctx := context.Background()
	db, err := platform.Open(ctx, url)
	if err != nil {
		t.Fatal(err)
	}
	defer db.Close()
	if err = platform.Migrate(ctx, db.DB); err != nil {
		t.Fatal(err)
	}
	app := New(db, "test-secret")
	var author, other, article int64
	suffix := randomURL(8)
	for _, item := range []struct {
		name string
		id   *int64
	}{{"author_" + suffix, &author}, {"other_" + suffix, &other}} {
		if err = db.DB.QueryRowContext(ctx, "INSERT INTO users(username,email,password_hash) VALUES($1,$2,'unused') RETURNING id", item.name, item.name+"@test.invalid").Scan(item.id); err != nil {
			t.Fatal(err)
		}
	}
	defer db.DB.ExecContext(ctx, "DELETE FROM users WHERE id IN ($1,$2)", author, other)
	slug := "draft-" + suffix
	if err = db.DB.QueryRowContext(ctx, "INSERT INTO articles(author_id,slug,title,description,body,status) VALUES($1,$2,'Draft','description','first','draft') RETURNING id", author, slug).Scan(&article); err != nil {
		t.Fatal(err)
	}
	if _, err = app.recordBySlug(ctx, slug, other); err == nil || err.(failure).Status != 404 {
		t.Fatalf("draft leaked to another user: %v", err)
	}
	if _, err = app.recordBySlug(ctx, slug, author); err != nil {
		t.Fatal(err)
	}
	input := func(body string) map[string]json.RawMessage {
		return map[string]json.RawMessage{"body": json.RawMessage(`"` + body + `"`)}
	}
	var wg sync.WaitGroup
	results := make(chan error, 2)
	for _, body := range []string{"second", "third"} {
		wg.Add(1)
		go func(body string) {
			defer wg.Done()
			_, err := app.saveArticle(ctx, article, author, input(body), true, 1, false, "", "")
			results <- err
		}(body)
	}
	wg.Wait()
	close(results)
	success, conflict := 0, 0
	for err := range results {
		if err == nil {
			success++
		} else if f, ok := err.(failure); ok && f.Status == 409 {
			conflict++
		} else {
			t.Fatalf("unexpected concurrent save error: %v", err)
		}
	}
	if success != 1 || conflict != 1 {
		t.Fatalf("concurrent saves: success=%d conflict=%d", success, conflict)
	}
	request := func() *httptest.ResponseRecorder {
		req := httptest.NewRequest("POST", "/api/articles/"+slug+"/publish", nil)
		req.Header.Set("Authorization", "Token "+app.token(author))
		route := chi.NewRouteContext()
		route.URLParams.Add("slug", slug)
		req = req.WithContext(context.WithValue(req.Context(), chi.RouteCtxKey, route))
		w := httptest.NewRecorder()
		if err := app.publishArticle(w, req); err != nil {
			t.Fatal(err)
		}
		return w
	}
	for i := 0; i < 2; i++ {
		w := request()
		if w.Code != 200 {
			t.Fatalf("publish status %d", w.Code)
		}
		var body struct {
			Article ArticleView `json:"article"`
		}
		if err = json.Unmarshal(w.Body.Bytes(), &body); err != nil {
			t.Fatal(err)
		}
		if body.Article.Status != "published" || body.Article.Revision != 3 || body.Article.PublishedAt == nil {
			t.Fatalf("publish transition: %+v", body.Article)
		}
	}
	if _, err = app.recordBySlug(ctx, slug, other); err != nil {
		t.Fatalf("published article invisible: %v", err)
	}
}

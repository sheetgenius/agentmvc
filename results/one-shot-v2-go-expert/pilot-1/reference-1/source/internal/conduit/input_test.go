package conduit

import (
	"encoding/json"
	"errors"
	"net/http/httptest"
	"strings"
	"testing"
)

func TestRevisionPresenceAndType(t *testing.T) {
	for _, tc := range []struct {
		body    string
		present bool
		invalid bool
		value   int
	}{
		{`{}`, false, false, 0},
		{`{"revision":null}`, true, true, 0},
		{`{"revision":"1"}`, true, true, 0},
		{`{"revision":1.5}`, true, true, 0},
		{`{"revision":1}`, true, false, 1},
	} {
		t.Run(tc.body, func(t *testing.T) {
			var fields map[string]json.RawMessage
			if err := json.Unmarshal([]byte(tc.body), &fields); err != nil {
				t.Fatal(err)
			}
			value, present, err := integer(fields, "revision")
			if value != tc.value || present != tc.present || (err != nil) != tc.invalid {
				t.Fatalf("got (%d,%v,%v)", value, present, err)
			}
			if tc.invalid {
				var problem failure
				if !errors.As(err, &problem) || problem.Status != 422 {
					t.Fatalf("invalid revision should be 422: %v", err)
				}
			}
		})
	}
}

func TestSharedEnvelopeIsStrict(t *testing.T) {
	for _, body := range []string{
		`{"article":{"revision":1},"extra":true}`,
		`{"article":null}`,
		`{"extra":{}}`,
		`{"article":{"revision":1}} {"extra":true}`,
	} {
		request := httptest.NewRequest("PUT", "/", strings.NewReader(body))
		if _, err := decodeShared(request); err == nil {
			t.Errorf("accepted shared envelope %s", body)
		}
	}
	valid := `{"article":{"revision":1,"body":"changed"}}`
	if _, err := decodeShared(httptest.NewRequest("PUT", "/", strings.NewReader(valid))); err != nil {
		t.Fatalf("valid shared envelope: %v", err)
	}
	general := `{"article":{"revision":1},"extra":true}`
	if _, err := decode(httptest.NewRequest("PUT", "/", strings.NewReader(general)), "article"); err != nil {
		t.Fatalf("general API must continue to ignore unrelated outer fields: %v", err)
	}
}

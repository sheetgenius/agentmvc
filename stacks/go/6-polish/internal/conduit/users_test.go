package conduit

import (
	"strings"
	"testing"

	"golang.org/x/crypto/bcrypt"
)

func TestPasswordLengthUsesCharacters(t *testing.T) {
	password := strings.Repeat("界", 64)
	hash, err := passwordHash(password)
	if err != nil {
		t.Fatal(err)
	}
	if err := bcrypt.CompareHashAndPassword([]byte(hash), passwordDigest(password)); err != nil {
		t.Fatal(err)
	}
	if _, err := passwordHash(strings.Repeat("界", 7)); err == nil {
		t.Fatal("seven characters must be rejected")
	}
}

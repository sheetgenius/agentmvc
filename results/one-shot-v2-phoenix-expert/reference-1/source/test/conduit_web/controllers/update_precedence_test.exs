defmodule ConduitWeb.UpdatePrecedenceTest do
  use ConduitWeb.ConnCase

  alias Conduit.{Accounts, Articles}

  test "ownership and visibility precede malformed update envelopes" do
    owner = user("owner")
    stranger = user("stranger")

    {:ok, article} =
      Articles.create(owner, %{"title" => "Precedence", "description" => "d", "body" => "b"})

    {:ok, draft} =
      Articles.create(owner, %{
        "title" => "Private precedence",
        "description" => "d",
        "body" => "b",
        "status" => "draft"
      })

    assert status(owner, article.slug, %{"article" => %{"body" => "updated"}}) == 200
    assert status(stranger, article.slug, %{"article" => %{"body" => "b"}}) == 403
    assert status(stranger, article.slug, %{"article" => "invalid"}) == 403
    assert status(stranger, draft.slug, %{"article" => "invalid"}) == 404
    assert status(owner, "missing-precedence", %{"article" => %{"body" => "b"}}) == 404
    assert status(owner, "missing-precedence", %{"article" => "invalid"}) == 404
  end

  defp user(label) do
    name = "#{label}_#{System.unique_integer([:positive])}"

    {:ok, user} =
      Accounts.register(%{
        "username" => name,
        "email" => "#{name}@test.com",
        "password" => "password123"
      })

    user
  end

  defp status(user, slug, payload) do
    conn =
      build_conn()
      |> put_req_header("authorization", "Token " <> Accounts.token(user))
      |> put_req_header("content-type", "application/json")
      |> put("/api/articles/" <> slug, Jason.encode!(payload))

    conn.status
  end
end

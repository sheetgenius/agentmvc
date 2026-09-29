defmodule Conduit.RulesTest do
  use Conduit.DataCase

  alias Conduit.{Accounts, Articles, Exports, Shares}

  defp user(label) do
    unique = "#{label}_#{System.unique_integer([:positive])}"

    {:ok, user} =
      Accounts.register(%{
        "username" => unique,
        "email" => "#{unique}@test.com",
        "password" => "password123"
      })

    user
  end

  defp article(author, attrs \\ %{}) do
    {:ok, article} =
      Articles.create(
        author,
        Map.merge(
          %{"title" => "A title", "description" => "description", "body" => "body"},
          attrs
        )
      )

    article
  end

  test "draft visibility and discovery change only on publication" do
    author = user("author")
    reader = user("reader")
    draft = article(author, %{"status" => "draft", "tagList" => ["private-tag"]})

    assert {:ok, _} = Articles.get_visible(draft.slug, {:user, author})
    assert {:error, {:article, "not found"}} = Articles.get_visible(draft.slug, {:user, reader})
    assert {:error, {:article, "not found"}} = Articles.get_visible(draft.slug, :anonymous)

    assert {:error, {:article, "is a draft"}} =
             Articles.get_published(draft.slug, {:user, author})

    assert {[], 0} = Articles.list(:global, {:user, author}, %{"tag" => "private-tag"})
    refute "private-tag" in Articles.tags()

    assert {:ok, published} = Articles.publish(author, draft.slug)
    assert published.revision == 2
    assert published.published_at
    assert {:ok, same} = Articles.publish(author, draft.slug)
    assert same.revision == 2
    assert {[_], 1} = Articles.list(:global, :anonymous, %{"tag" => "private-tag"})
  end

  test "shared edits use the same revision rule and revocation ends capability" do
    author = user("editor")
    draft = article(author, %{"status" => "draft"})
    assert {:ok, share} = Shares.create(author, draft.slug)
    attrs = %{"title" => "New title", "body" => "new body", "revision" => 1}

    assert {:ok, edited} = Articles.commit({:share, share.id, share.key}, attrs)
    assert edited.revision == 2
    assert edited.slug != draft.slug
    assert {:ok, same_article} = Shares.article(share.id, share.key)
    assert same_article.id == draft.id
    assert {:error, {:stale, current}} = Articles.commit({:share, share.id, share.key}, attrs)
    assert current.revision == 2
    assert current.body == "new body"

    assert :ok = Shares.revoke(author, edited.slug)
    assert {:error, {:share, "not found"}} = Shares.article(share.id, share.key)
    assert {:error, {:share, "not found"}} = Articles.commit({:share, share.id, share.key}, attrs)
  end

  test "export completion snapshots drafts and comment counts" do
    author = user("exporter")
    published = article(author)
    _draft = article(author, %{"title" => "Draft", "status" => "draft"})
    assert {:ok, _} = Articles.create_comment(author, published, %{"body" => "comment"})
    assert {:ok, export} = Exports.start(author)
    assert export.status == "pending"
    assert {:ok, _} = Exports.complete(export.id)
    assert {:ok, done} = Exports.get(author, Integer.to_string(export.id))
    assert Enum.map(done.articles, & &1["status"]) == ["published", "draft"]
    assert hd(done.articles)["commentsCount"] == 1
    assert {:ok, _} = Articles.delete(author, published.slug)
    assert {:ok, snapshot} = Exports.get(author, Integer.to_string(export.id))
    assert snapshot.articles == done.articles
  end
end

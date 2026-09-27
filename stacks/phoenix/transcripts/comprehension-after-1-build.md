# phoenix · comprehension after-1-build

| | |
| --- | --- |
| Codex session | `01a0e0c3-3051-7ed3-95aa-a4571a2403f4` |
| Started, finished (UTC) | 2026-09-27T02:48:03Z, 2026-09-27T02:49:25Z (82 s) |
| Exit code | 0 |
| Agent tokens (uncached input + output) | 18,834 |
| Prompt | [steps/comprehension.md](../../../steps/comprehension.md) |
| Raw events | [comprehension-after-1-build.jsonl](comprehension-after-1-build.jsonl) |

Outputs longer than 40 lines are cut here; the `.jsonl` file next to this one has them in full.

**Agent:**

I’ll trace the route handlers, models, and response serializers needed for these rules. I’ll only read files in this directory and won’t run the app or tests.

```sh
$ /bin/zsh -lc "pwd && rg --files -g 'AGENTS.md' -g '"'!node_modules'"' -g '"'!_build'"' -g '"'!deps'"' -g '"'!vendor'"' | sort && rg --files -g '"'!node_modules'"' -g '"'!_build'"' -g '"'!deps'"' -g '"'!vendor'"' | head -120"
```
<details><summary>output (exit 0)</summary>

```
/work/app
lib/conduit_web.ex
lib/conduit/repo.ex
lib/conduit/content.ex
lib/conduit/application.ex
lib/conduit/accounts/user.ex
lib/conduit/accounts.ex
lib/conduit/content/article.ex
lib/conduit/content/comment.ex
lib/conduit_web/controllers/article_controller.ex
lib/conduit_web/controllers/profile_controller.ex
lib/conduit_web/controllers/comment_controller.ex
lib/conduit_web/controllers/fallback_controller.ex
lib/conduit_web/controllers/error_json.ex
lib/conduit_web/controllers/user_controller.ex
lib/conduit_web/endpoint.ex
lib/conduit_web/router.ex
lib/conduit_web/presenter.ex
lib/conduit_web/auth.ex
priv/repo/migrations/20260927021412_create_conduit.exs
config/prod.exs
config/config.exs
config/dev.exs
config/runtime.exs
mix.exs
```

</details>

```sh
$ /bin/zsh -lc "rg -n 'slug|tagList|tags|favorite|feed|limit|bio|password|token|delete|update|unique|422|403|401|forbidden' lib priv/repo/migrations mix.exs"
```
<details><summary>output (exit 0)</summary>

```
priv/repo/migrations/20260927021412_create_conduit.exs:8:      add :password_hash, :string, null: false
priv/repo/migrations/20260927021412_create_conduit.exs:9:      add :bio, :text
priv/repo/migrations/20260927021412_create_conduit.exs:14:    create unique_index(:users, [:username])
priv/repo/migrations/20260927021412_create_conduit.exs:15:    create unique_index(:users, [:email])
priv/repo/migrations/20260927021412_create_conduit.exs:18:      add :slug, :string, null: false
priv/repo/migrations/20260927021412_create_conduit.exs:23:      add :author_id, references(:users, on_delete: :delete_all), null: false
priv/repo/migrations/20260927021412_create_conduit.exs:27:    create unique_index(:articles, [:slug])
priv/repo/migrations/20260927021412_create_conduit.exs:32:      add :author_id, references(:users, on_delete: :delete_all), null: false
priv/repo/migrations/20260927021412_create_conduit.exs:33:      add :article_id, references(:articles, on_delete: :delete_all), null: false
priv/repo/migrations/20260927021412_create_conduit.exs:40:      add :follower_id, references(:users, on_delete: :delete_all), null: false
priv/repo/migrations/20260927021412_create_conduit.exs:41:      add :followed_id, references(:users, on_delete: :delete_all), null: false
priv/repo/migrations/20260927021412_create_conduit.exs:44:    create unique_index(:follows, [:follower_id, :followed_id])
priv/repo/migrations/20260927021412_create_conduit.exs:46:    create table(:favorites, primary_key: false) do
priv/repo/migrations/20260927021412_create_conduit.exs:47:      add :user_id, references(:users, on_delete: :delete_all), null: false
priv/repo/migrations/20260927021412_create_conduit.exs:48:      add :article_id, references(:articles, on_delete: :delete_all), null: false
priv/repo/migrations/20260927021412_create_conduit.exs:51:    create unique_index(:favorites, [:user_id, :article_id])
lib/conduit/content.ex:7:  def fetch_article(slug) do
lib/conduit/content.ex:8:    case Repo.get_by(Article, slug: slug) do
lib/conduit/content.ex:21:  def update_article(article, attrs) do
lib/conduit/content.ex:22:    article |> Article.changeset(attrs) |> Repo.update() |> preload_author()
lib/conduit/content.ex:25:  def delete_article(article), do: Repo.delete(article)
lib/conduit/content.ex:31:      |> filter(:favorited, params["favorited"])
lib/conduit/content.ex:37:  def feed(viewer, params) do
lib/conduit/content.ex:44:  def tags do
lib/conduit/content.ex:51:  def favorite(viewer, article) do
lib/conduit/content.ex:52:    Repo.insert_all("favorites", [%{user_id: viewer.id, article_id: article.id}],
lib/conduit/content.ex:59:  def unfavorite(viewer, article) do
lib/conduit/content.ex:60:    Repo.delete_all(
lib/conduit/content.ex:61:      from f in "favorites", where: f.user_id == ^viewer.id and f.article_id == ^article.id
lib/conduit/content.ex:67:  def favorited?(nil, _article), do: false
lib/conduit/content.ex:69:  def favorited?(viewer, article) do
lib/conduit/content.ex:70:    Repo.exists?(from a in Ecto.assoc(viewer, :favorites), where: a.id == ^article.id)
lib/conduit/content.ex:73:  def favorites_count(article), do: Repo.aggregate(Ecto.assoc(article, :fans), :count, :id)
lib/conduit/content.ex:92:  def delete_comment(comment), do: Repo.delete(comment)
lib/conduit/content.ex:99:  defp filter(query, :favorited, username) do
lib/conduit/content.ex:101:    |> join(:inner, [a], f in "favorites", on: f.article_id == a.id)
lib/conduit/content.ex:109:    limit = positive_integer(params["limit"], 20)
lib/conduit/content.ex:115:      |> limit(^limit)
lib/conduit_web/controllers/article_controller.ex:12:  def feed(conn, params) do
lib/conduit_web/controllers/article_controller.ex:13:    render_list(conn, Content.feed(conn.assigns.current_user, params))
[... 105 more lines]
```

</details>

```sh
$ /bin/zsh -lc "cat 'lib/conduit/content/article.ex'"
```
<details><summary>output (exit 0)</summary>

```
defmodule Conduit.Content.Article do
  use Ecto.Schema
  import Ecto.Changeset

  schema "articles" do
    field :slug, :string
    field :title, :string
    field :description, :string
    field :body, :string
    field :tag_list, {:array, :string}, default: []
    belongs_to :author, Conduit.Accounts.User
    has_many :comments, Conduit.Content.Comment

    many_to_many :fans, Conduit.Accounts.User,
      join_through: "favorites",
      join_keys: [article_id: :id, user_id: :id]

    timestamps(type: :utc_datetime_usec)
  end

  def changeset(article, attrs) do
    attrs =
      if Map.has_key?(attrs, "tagList"),
        do: Map.put(attrs, "tag_list", attrs["tagList"]),
        else: attrs

    article
    |> cast(attrs, [:title, :description, :body, :tag_list])
    |> validate_required([:title, :description, :body])
    |> reject_null_tags(attrs)
    |> slug_from_title()
    |> unique_constraint(:slug)
  end

  defp reject_null_tags(changeset, %{"tagList" => nil}),
    do: add_error(changeset, :tag_list, "can't be blank")

  defp reject_null_tags(changeset, _attrs), do: changeset

  defp slug_from_title(changeset) do
[... 12 more lines]
```

</details>

```sh
$ /bin/zsh -lc "cat 'lib/conduit/content.ex'"
```
<details><summary>output (exit 0)</summary>

```
defmodule Conduit.Content do
  import Ecto.Query
  alias Conduit.Content.{Article, Comment}
  alias Conduit.Accounts.User
  alias Conduit.Repo

  def fetch_article(slug) do
    case Repo.get_by(Article, slug: slug) do
      nil -> {:error, :article}
      article -> {:ok, Repo.preload(article, :author)}
    end
  end

  def create_article(author, attrs) do
    %Article{author_id: author.id}
    |> Article.changeset(attrs)
    |> Repo.insert()
    |> preload_author()
  end

  def update_article(article, attrs) do
    article |> Article.changeset(attrs) |> Repo.update() |> preload_author()
  end

  def delete_article(article), do: Repo.delete(article)

  def list_articles(params) do
    query =
      Article
      |> filter(:author, params["author"])
      |> filter(:favorited, params["favorited"])
      |> filter(:tag, params["tag"])

    page(query, params)
  end

  def feed(viewer, params) do
    Article
    |> join(:inner, [a], f in "follows", on: f.followed_id == a.author_id)
    |> where([a, f], f.follower_id == ^viewer.id)
[... 94 more lines]
```

</details>

```sh
$ /bin/zsh -lc "cat 'lib/conduit_web/controllers/comment_controller.ex'"
```
<details><summary>output (exit 0)</summary>

```
defmodule ConduitWeb.CommentController do
  use ConduitWeb, :controller
  alias Conduit.Content
  alias ConduitWeb.Presenter

  action_fallback ConduitWeb.FallbackController

  def index(conn, %{"slug" => slug}) do
    with {:ok, article} <- Content.fetch_article(slug) do
      comments = Content.list_comments(article)

      json(conn, %{
        comments: Enum.map(comments, &Presenter.comment(&1, conn.assigns.current_user))
      })
    end
  end

  def create(conn, %{"slug" => slug, "comment" => attrs}) do
    with {:ok, article} <- Content.fetch_article(slug),
         {:ok, comment} <- Content.create_comment(article, conn.assigns.current_user, attrs) do
      conn
      |> put_status(:created)
      |> json(%{comment: Presenter.comment(comment, conn.assigns.current_user)})
    end
  end

  def delete(conn, %{"slug" => slug, "id" => id}) do
    with {:ok, article} <- Content.fetch_article(slug),
         {:ok, comment} <- find_comment(article, id),
         :ok <- owner(comment, conn.assigns.current_user),
         {:ok, _} <- Content.delete_comment(comment) do
      send_resp(conn, :no_content, "")
    end
  end

  defp find_comment(article, id) do
    with {id, ""} <- Integer.parse(id),
         %{} = comment <- Content.get_comment(article, id) do
      {:ok, comment}
    else
[... 7 more lines]
```

</details>

```sh
$ /bin/zsh -lc "cat 'lib/conduit_web/controllers/article_controller.ex'"
```
<details><summary>output (exit 0)</summary>

```
defmodule ConduitWeb.ArticleController do
  use ConduitWeb, :controller
  alias Conduit.Content
  alias ConduitWeb.Presenter

  action_fallback ConduitWeb.FallbackController

  def index(conn, params) do
    render_list(conn, Content.list_articles(params))
  end

  def feed(conn, params) do
    render_list(conn, Content.feed(conn.assigns.current_user, params))
  end

  def show(conn, %{"slug" => slug}) do
    with {:ok, article} <- Content.fetch_article(slug) do
      json(conn, %{article: Presenter.article(article, conn.assigns.current_user)})
    end
  end

  def create(conn, %{"article" => attrs}) do
    with {:ok, article} <- Content.create_article(conn.assigns.current_user, attrs) do
      conn
      |> put_status(:created)
      |> json(%{article: Presenter.article(article, conn.assigns.current_user)})
    end
  end

  def update(conn, %{"slug" => slug, "article" => attrs}) do
    with {:ok, article} <- Content.fetch_article(slug),
         :ok <- owner(article, conn.assigns.current_user),
         {:ok, article} <- Content.update_article(article, attrs) do
      json(conn, %{article: Presenter.article(article, conn.assigns.current_user)})
    end
  end

  def delete(conn, %{"slug" => slug}) do
    with {:ok, article} <- Content.fetch_article(slug),
         :ok <- owner(article, conn.assigns.current_user),
[... 31 more lines]
```

</details>

```sh
$ /bin/zsh -lc "cat 'lib/conduit/accounts/user.ex'"
```
<details><summary>output (exit 0)</summary>

```
defmodule Conduit.Accounts.User do
  use Ecto.Schema
  import Ecto.Changeset

  schema "users" do
    field :username, :string
    field :email, :string
    field :password, :string, virtual: true, redact: true
    field :password_hash, :string, redact: true
    field :bio, :string
    field :image, :string

    many_to_many :following, __MODULE__,
      join_through: "follows",
      join_keys: [follower_id: :id, followed_id: :id]

    many_to_many :favorites, Conduit.Content.Article, join_through: "favorites"
    timestamps(type: :utc_datetime_usec)
  end

  def registration_changeset(user, attrs) do
    user
    |> cast(attrs, [:username, :email, :password])
    |> validate_required([:username, :email, :password])
    |> validate_length(:password, min: 8)
    |> validate_format(:email, ~r/^[^\s@]+@[^\s@]+\.[^\s@]+$/)
    |> unique_constraint(:username)
    |> unique_constraint(:email)
    |> hash_password()
  end

  def update_changeset(user, attrs) do
    user
    |> cast(attrs, [:username, :email, :password, :bio, :image])
    |> validate_required([:username, :email])
    |> validate_format(:email, ~r/^[^\s@]+@[^\s@]+\.[^\s@]+$/)
    |> maybe_validate_password(attrs)
    |> unique_constraint(:username)
    |> unique_constraint(:email)
    |> hash_password()
[... 22 more lines]
```

</details>

```sh
$ /bin/zsh -lc "cat 'lib/conduit_web/controllers/fallback_controller.ex'"
```
<details><summary>output (exit 0)</summary>

```
defmodule ConduitWeb.FallbackController do
  use ConduitWeb, :controller

  def call(conn, {:error, %Ecto.Changeset{} = changeset}) do
    errors =
      changeset
      |> Ecto.Changeset.traverse_errors(fn {message, opts} ->
        Enum.reduce(opts, message, fn {key, value}, text ->
          String.replace(text, "%{#{key}}", to_string(value))
        end)
      end)
      |> Map.new(fn {field, messages} -> {error_field(field), messages} end)

    status =
      if Enum.any?(errors, fn {_, messages} -> "has already been taken" in messages end),
        do: :conflict,
        else: :unprocessable_entity

    conn |> put_status(status) |> json(%{errors: errors})
  end

  def call(conn, {:error, :credentials}), do: error(conn, :unauthorized, :credentials, "invalid")
  def call(conn, {:error, resource}), do: error(conn, :not_found, resource, "not found")
  def call(conn, {:forbidden, resource}), do: error(conn, :forbidden, resource, "forbidden")
  def call(conn, {:blank, field}), do: error(conn, :unprocessable_entity, field, "can't be blank")

  defp error(conn, status, field, message),
    do: conn |> put_status(status) |> json(%{errors: %{field => [message]}})

  defp error_field(:tag_list), do: "tagList"
  defp error_field(field), do: field
end
```

</details>

```sh
$ /bin/zsh -lc "cat 'lib/conduit/accounts.ex'"
```
<details><summary>output (exit 0)</summary>

```
defmodule Conduit.Accounts do
  import Ecto.Query
  alias Conduit.Accounts.User
  alias Conduit.Repo

  def register(attrs), do: %User{} |> User.registration_changeset(attrs) |> Repo.insert()
  def update(user, attrs), do: user |> User.update_changeset(attrs) |> Repo.update()
  def get_user(id), do: Repo.get(User, id)
  def get_profile(username), do: Repo.get_by(User, username: username)

  def authenticate(email, password) do
    case Repo.get_by(User, email: email) do
      nil ->
        Bcrypt.no_user_verify()
        {:error, :credentials}

      user ->
        if Bcrypt.verify_pass(password, user.password_hash),
          do: {:ok, user},
          else: {:error, :credentials}
    end
  end

  def token(user) do
    {:ok, token, _claims} =
      Joken.generate_and_sign(token_claims(), %{"sub" => to_string(user.id)}, signer())

    token
  end

  def from_token(token) do
    with {:ok, %{"sub" => id}} <- Joken.verify_and_validate(token_claims(), token, signer()),
         {id, ""} <- Integer.parse(id),
         %User{} = user <- get_user(id) do
      {:ok, user}
    else
      _ -> {:error, :token}
    end
  end

[... 25 more lines]
```

</details>

```sh
$ /bin/zsh -lc "cat 'lib/conduit_web/controllers/user_controller.ex'"
```
<details><summary>output (exit 0)</summary>

```
defmodule ConduitWeb.UserController do
  use ConduitWeb, :controller
  alias Conduit.Accounts
  alias ConduitWeb.Presenter

  action_fallback ConduitWeb.FallbackController

  def create(conn, %{"user" => attrs}) do
    with {:ok, user} <- Accounts.register(attrs) do
      conn |> put_status(:created) |> json(%{user: Presenter.user(user)})
    end
  end

  def login(conn, %{"user" => %{"email" => email, "password" => password}})
      when is_binary(email) and byte_size(email) > 0 and is_binary(password) and
             byte_size(password) > 0 do
    with {:ok, user} <- Accounts.authenticate(email, password) do
      json(conn, %{user: Presenter.user(user)})
    end
  end

  def login(_conn, %{"user" => attrs}) do
    field = if is_binary(attrs["email"]) and attrs["email"] != "", do: :password, else: :email
    {:blank, field}
  end

  def show(conn, _params), do: json(conn, %{user: Presenter.user(conn.assigns.current_user)})

  def update(conn, %{"user" => attrs}) do
    with {:ok, user} <- Accounts.update(conn.assigns.current_user, attrs) do
      json(conn, %{user: Presenter.user(user)})
    end
  end
end
```

</details>

```sh
$ /bin/zsh -lc "cat 'lib/conduit_web/presenter.ex'"
```
<details><summary>output (exit 0)</summary>

```
defmodule ConduitWeb.Presenter do
  alias Conduit.{Accounts, Content}

  def user(user) do
    %{
      email: user.email,
      username: user.username,
      bio: user.bio,
      image: user.image,
      token: Accounts.token(user)
    }
  end

  def profile(user, viewer) do
    %{
      username: user.username,
      bio: user.bio,
      image: user.image,
      following: Accounts.following?(viewer, user)
    }
  end

  def article(article, viewer, body? \\ true) do
    data = %{
      slug: article.slug,
      title: article.title,
      description: article.description,
      tagList: article.tag_list,
      createdAt: article.inserted_at,
      updatedAt: article.updated_at,
      favorited: Content.favorited?(viewer, article),
      favoritesCount: Content.favorites_count(article),
      author: profile(article.author, viewer)
    }

    if body?, do: Map.put(data, :body, article.body), else: data
  end

  def comment(comment, viewer) do
    %{
[... 8 more lines]
```

</details>

```sh
$ /bin/zsh -lc "cat 'lib/conduit_web/router.ex'"
```
<details><summary>output (exit 0)</summary>

```
defmodule ConduitWeb.Router do
  use ConduitWeb, :router

  pipeline :api do
    plug :accepts, ["json"]
    plug ConduitWeb.Auth, :fetch_user
  end

  pipeline :authenticated do
    plug ConduitWeb.Auth, :require_user
  end

  scope "/api", ConduitWeb do
    pipe_through [:api, :authenticated]

    get "/user", UserController, :show
    put "/user", UserController, :update
    post "/profiles/:username/follow", ProfileController, :follow
    delete "/profiles/:username/follow", ProfileController, :unfollow
    get "/articles/feed", ArticleController, :feed
    post "/articles", ArticleController, :create
    put "/articles/:slug", ArticleController, :update
    delete "/articles/:slug", ArticleController, :delete
    post "/articles/:slug/favorite", ArticleController, :favorite
    delete "/articles/:slug/favorite", ArticleController, :unfavorite
    post "/articles/:slug/comments", CommentController, :create
    delete "/articles/:slug/comments/:id", CommentController, :delete
  end

  scope "/api", ConduitWeb do
    pipe_through :api

    post "/users", UserController, :create
    post "/users/login", UserController, :login
    get "/profiles/:username", ProfileController, :show
    get "/articles", ArticleController, :index
    get "/articles/:slug", ArticleController, :show
    get "/articles/:slug/comments", CommentController, :index
    get "/tags", ArticleController, :tags
  end
[... 1 more lines]
```

</details>

```sh
$ /bin/zsh -lc "cat 'priv/repo/migrations/20260927021412_create_conduit.exs'"
```
<details><summary>output (exit 0)</summary>

```
defmodule Conduit.Repo.Migrations.CreateConduit do
  use Ecto.Migration

  def change do
    create table(:users) do
      add :username, :string, null: false
      add :email, :string, null: false
      add :password_hash, :string, null: false
      add :bio, :text
      add :image, :string
      timestamps(type: :utc_datetime_usec)
    end

    create unique_index(:users, [:username])
    create unique_index(:users, [:email])

    create table(:articles) do
      add :slug, :string, null: false
      add :title, :string, null: false
      add :description, :text, null: false
      add :body, :text, null: false
      add :tag_list, {:array, :string}, null: false, default: []
      add :author_id, references(:users, on_delete: :delete_all), null: false
      timestamps(type: :utc_datetime_usec)
    end

    create unique_index(:articles, [:slug])
    create index(:articles, [:author_id])

    create table(:comments) do
      add :body, :text, null: false
      add :author_id, references(:users, on_delete: :delete_all), null: false
      add :article_id, references(:articles, on_delete: :delete_all), null: false
      timestamps(type: :utc_datetime_usec)
    end

    create index(:comments, [:article_id])

    create table(:follows, primary_key: false) do
      add :follower_id, references(:users, on_delete: :delete_all), null: false
[... 13 more lines]
```

</details>

```sh
$ /bin/zsh -lc "cat 'mix.exs'"
```
<details><summary>output (exit 0)</summary>

```
defmodule Conduit.MixProject do
  use Mix.Project

  def project do
    [
      app: :conduit,
      version: "0.1.0",
      elixir: "~> 1.17",
      start_permanent: Mix.env() == :prod,
      deps: deps()
    ]
  end

  def application, do: [mod: {Conduit.Application, []}, extra_applications: [:logger]]

  defp deps do
    [
      {:phoenix, "~> 1.8.15"},
      {:ecto_sql, "~> 3.13"},
      {:postgrex, ">= 0.0.0"},
      {:jason, "~> 1.2"},
      {:bandit, "~> 1.5"},
      {:bcrypt_elixir, "~> 3.2"},
      {:joken, "~> 2.6"},
      {:cors_plug, "~> 3.0"}
    ]
  end
end
```

</details>

**Agent:**

The main rules are in the Ecto changesets, `Content`, and the controller fallback. I’m checking local configuration for a token lifetime before I finalize that answer.

```sh
$ /bin/zsh -lc "rg -n -i 'joken|token|expir|ttl|default_claims|empty_values|bcrypt' config lib priv mix.exs"
```
<details><summary>output (exit 0)</summary>

```
mix.exs:23:      {:bcrypt_elixir, "~> 3.2"},
mix.exs:24:      {:joken, "~> 2.6"},
lib/conduit/accounts.ex:14:        Bcrypt.no_user_verify()
lib/conduit/accounts.ex:18:        if Bcrypt.verify_pass(password, user.password_hash),
lib/conduit/accounts.ex:24:  def token(user) do
lib/conduit/accounts.ex:25:    {:ok, token, _claims} =
lib/conduit/accounts.ex:26:      Joken.generate_and_sign(token_claims(), %{"sub" => to_string(user.id)}, signer())
lib/conduit/accounts.ex:28:    token
lib/conduit/accounts.ex:31:  def from_token(token) do
lib/conduit/accounts.ex:32:    with {:ok, %{"sub" => id}} <- Joken.verify_and_validate(token_claims(), token, signer()),
lib/conduit/accounts.ex:37:      _ -> {:error, :token}
lib/conduit/accounts.ex:63:  defp signer, do: Joken.Signer.create("HS256", ConduitWeb.Endpoint.config(:secret_key_base))
lib/conduit/accounts.ex:64:  defp token_claims, do: Joken.Config.default_claims(skip: [:iss, :aud, :jti])
lib/conduit/accounts/user.ex:56:        put_change(changeset, :password_hash, Bcrypt.hash_pwd_salt(password))
lib/conduit_web/auth.ex:11:      ["Token " <> token] ->
lib/conduit_web/auth.ex:12:        case Accounts.from_token(token) do
lib/conduit_web/auth.ex:31:    |> send_resp(401, Jason.encode!(%{errors: %{token: [message]}}))
lib/conduit_web/presenter.ex:10:      token: Accounts.token(user)
```

</details>

**Agent:**

## 1
Answer: The title is lowercased, runs of non-ASCII letters or digits become hyphens, and leading or trailing hyphens are removed; the first eight characters of a generated UUID are appended. Changing the title generates a new slug; omitting or leaving the title unchanged does not.
Where: `lib/conduit/content/article.ex` — `slug_from_title/1`
Confidence: high

## 2
Answer: A duplicate email or username returns HTTP 409 with `{"errors":{"email":["has already been taken"]}}` or the equivalent `username` field; both fields can appear if both conflict. The fallback decides the status and response body from the changeset errors.
Where: `lib/conduit/accounts/user.ex` — `registration_changeset/2`; `lib/conduit_web/controllers/fallback_controller.ex` — `call/2`
Confidence: high

## 3
Answer: The feed contains articles by users the authenticated viewer follows. It orders them by creation time descending, then article ID descending, before applying pagination.
Where: `lib/conduit/content.ex` — `feed/2`, `page/2`
Confidence: high

## 4
Answer: `favoritesCount` is a database count of users associated with the article through the `favorites` join table.
Where: `lib/conduit_web/presenter.ex` — `article/3`; `lib/conduit/content.ex` — `favorites_count/1`
Confidence: high

## 5
Answer: The request returns HTTP 403 with `{"errors":{"comment":["forbidden"]}}`.
Where: `lib/conduit_web/controllers/comment_controller.ex` — `delete/2`, `owner/2`; `lib/conduit_web/controllers/fallback_controller.ex` — `call/2`
Confidence: high

## 6
Answer: An empty string is treated as an empty value by Ecto’s `cast`, so the stored `bio` becomes `nil`.
Where: `lib/conduit/accounts/user.ex` — `update_changeset/2`
Confidence: high

## 7
Answer: Tags are stored as a string array in each article’s `tag_list` column. `GET /api/tags` flattens those arrays, removes duplicates, and returns the tags sorted ascending.
Where: `priv/repo/migrations/20260927021412_create_conduit.exs` — `change/0`; `lib/conduit/content.ex` — `tags/0`
Confidence: high

## 8
Answer: The default `limit` is 20. The code accepts nonnegative integers, including zero, and sets no maximum.
Where: `lib/conduit/content.ex` — `page/2`, `positive_integer/2`
Confidence: high

## 9
Answer: Joken creates a token signed with HS256 using the endpoint’s `secret_key_base`; its `sub` claim contains the user ID as a string. Expiry comes from Joken’s default claims, and this directory does not specify a lifetime.
Where: `lib/conduit/accounts.ex` — `token/1`, `signer/0`, `token_claims/0`
Confidence: high

## 10
Answer: The controller checks that the current user’s ID equals the article’s `author_id` before either update or delete proceeds.
Where: `lib/conduit_web/controllers/article_controller.ex` — `update/2`, `delete/2`, `owner/2`
Confidence: high

## 11
Answer: Omitting `tagList` leaves the existing tags unchanged. Sending `"tagList": null` adds a validation error, `"can't be blank"`, for `tagList`.
Where: `lib/conduit/content/article.ex` — `changeset/2`, `reject_null_tags/2`
Confidence: high

## 12
Answer: Passwords are stored as bcrypt hashes in `password_hash`; the plaintext `password` field is virtual. The `bcrypt_elixir` library supplies `Bcrypt.hash_pwd_salt/1`.
Where: `lib/conduit/accounts/user.ex` — `hash_password/1`, `schema "users"`; `mix.exs` — `deps/0`
Confidence: high

Files read: 12


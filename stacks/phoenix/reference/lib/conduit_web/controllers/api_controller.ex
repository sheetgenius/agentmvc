defmodule ConduitWeb.ApiController do
  use ConduitWeb, :controller
  alias Conduit.{Accounts, Content, Exports, RateLimiter, Repo}

  def register(conn, params),
    do:
      reply(conn, Accounts.register(params["user"]), fn user -> %{user: user_data(user)} end, 201)

  def login(conn, params) do
    email = get_in(params, ["user", "email"])
    result = Accounts.login(params["user"])

    result =
      case result do
        {:ok, _} ->
          RateLimiter.reset(email)
          result

        {:unauthorized, _} ->
          if RateLimiter.failed(email),
            do: {:limited, %{credentials: ["rate limited"]}},
            else: result

        _ ->
          result
      end

    reply(conn, result, fn user -> %{user: user_data(user)} end)
  end

  def current(conn, _), do: reply(conn, auth(conn), fn user -> %{user: user_data(user)} end)

  def update_user(conn, params) do
    reply(
      conn,
      with({:ok, user} <- auth(conn), do: Accounts.update(user, params["user"])),
      fn user -> %{user: user_data(user)} end
    )
  end

  def profile(conn, %{"username" => username}) do
    reply(conn, Accounts.profile(username, viewer(conn)), fn value -> %{profile: value} end)
  end

  def follow(conn, %{"username" => username}), do: follow_action(conn, username, true)
  def unfollow(conn, %{"username" => username}), do: follow_action(conn, username, false)

  defp follow_action(conn, username, action) do
    reply(
      conn,
      with({:ok, user} <- auth(conn), do: Accounts.follow(user, username, action)),
      fn value -> %{profile: value} end
    )
  end

  def articles(conn, params), do: json(conn, Content.list(params, viewer(conn)))

  def feed(conn, params),
    do: reply(conn, auth(conn), fn user -> Content.list(params, user, :feed) end)

  def drafts(conn, params),
    do: reply(conn, auth(conn), fn user -> Content.list(params, user, :drafts) end)

  def tags(conn, _), do: json(conn, %{tags: Content.tags()})

  def article_create(conn, params) do
    reply(
      conn,
      with({:ok, user} <- auth(conn), do: Content.create(user, params["article"])),
      fn article -> %{article: Content.represent(article, viewer(conn))} end,
      201
    )
  end

  def article_show(conn, %{"slug" => slug}) do
    reply(conn, Content.article(slug, viewer(conn)), fn article ->
      %{article: Content.represent(article, viewer(conn))}
    end)
  end

  def article_update(conn, %{"slug" => slug} = params) do
    result =
      with {:ok, user} <- auth(conn),
           {:ok, article} <- Content.owned(slug, user),
           do: Content.update(article, params["article"], user)

    reply(conn, result, fn article -> %{article: Content.represent(article, viewer(conn))} end)
  end

  def article_delete(conn, %{"slug" => slug}) do
    result =
      with {:ok, user} <- auth(conn), {:ok, article} <- Content.owned(slug, user) do
        Content.revoke(article)
        Repo.delete!(article)
        {:ok, nil}
      end

    reply(conn, result, fn _ -> nil end, 204)
  end

  def publish(conn, %{"slug" => slug}) do
    result =
      with {:ok, user} <- auth(conn),
           {:ok, article} <- Content.owned(slug, user),
           do: Content.publish(article)

    reply(conn, result, fn article -> %{article: Content.represent(article, viewer(conn))} end)
  end

  def comments(conn, %{"slug" => slug}) do
    reply(conn, Content.article(slug, viewer(conn)), fn article ->
      %{comments: Content.comments(article)}
    end)
  end

  def comment_create(conn, %{"slug" => slug} = params) do
    result =
      with {:ok, user} <- auth(conn),
           {:ok, article} <- Content.article(slug, user),
           do: Content.comment_create(article, user, params["comment"])

    reply(conn, result, fn comment -> %{comment: Content.comment(comment)} end, 201)
  end

  def comment_delete(conn, %{"slug" => slug, "id" => id}) do
    result =
      with {:ok, user} <- auth(conn),
           {:ok, article} <- Content.article(slug, user),
           :ok <- Content.comment_delete(article, id, user),
           do: {:ok, nil}

    reply(conn, result, fn _ -> nil end, 204)
  end

  def favorite(conn, %{"slug" => slug}), do: favorite_action(conn, slug, true)
  def unfavorite(conn, %{"slug" => slug}), do: favorite_action(conn, slug, false)

  defp favorite_action(conn, slug, add?) do
    result =
      with {:ok, user} <- auth(conn),
           {:ok, article} <- Content.article(slug, user),
           do: Content.favorite(article, user, add?)

    reply(conn, result, fn article -> %{article: Content.represent(article, viewer(conn))} end)
  end

  def share_create(conn, %{"slug" => slug}) do
    result =
      with {:ok, user} <- auth(conn),
           {:ok, article} <- Content.owned(slug, user),
           do: Content.share_create(article)

    reply(conn, result, fn share -> %{share: share} end, 201)
  end

  def share_delete(conn, %{"slug" => slug}) do
    result =
      with {:ok, user} <- auth(conn),
           {:ok, article} <- Content.owned(slug, user),
           :ok <- Content.revoke(article),
           do: {:ok, nil}

    reply(conn, result, fn _ -> nil end, 204)
  end

  def shared_show(conn, %{"id" => id}) do
    reply(conn, Content.shared_article(id, share_key(conn)), fn article ->
      %{article: Content.shared(article)}
    end)
  end

  def shared_update(conn, %{"id" => id} = params) do
    result =
      with {:ok, article} <- Content.shared_article(id, share_key(conn)),
           do: Content.update(article, params["article"], nil, true)

    reply(conn, result, fn article -> %{article: Content.shared(article)} end, 200, :shared)
  end

  def live(conn, %{"id" => id}),
    do: WebSockAdapter.upgrade(conn, ConduitWeb.LiveSocket, id, timeout: 60_000)

  def export_create(conn, _) do
    reply(
      conn,
      with({:ok, user} <- auth(conn), do: Exports.create(user)),
      fn export -> %{export: Exports.represent(export)} end,
      202
    )
  end

  def export_show(conn, %{"id" => id}) do
    reply(conn, with({:ok, user} <- auth(conn), do: Exports.get(user, id)), fn export ->
      %{export: Exports.represent(export)}
    end)
  end

  def options(conn, _), do: send_resp(conn, 204, "")
  def unknown(conn, _), do: conn |> put_status(404) |> json(%{errors: %{route: ["not found"]}})

  defp viewer(conn) do
    with ["Token " <> token] <- get_req_header(conn, "authorization"),
         do: Accounts.by_token(token),
         else: (_ -> nil)
  end

  defp auth(conn) do
    case viewer(conn) do
      nil -> {:unauthorized, %{token: ["is missing"]}}
      user -> {:ok, user}
    end
  end

  defp share_key(conn), do: List.first(get_req_header(conn, "x-share-key"))

  defp user_data(user),
    do: %{
      email: user.email,
      username: user.username,
      bio: user.bio,
      image: user.image,
      token: Accounts.token(user)
    }

  defp reply(conn, result, render, status \\ 200, shape \\ :article)

  defp reply(conn, {:ok, value}, render, status, _),
    do:
      if(status == 204,
        do: send_resp(conn, 204, ""),
        else: conn |> put_status(status) |> json(render.(value))
      )

  defp reply(conn, {:stale, article}, _, _, shape) do
    current =
      if shape == :shared,
        do: Content.shared(article),
        else: Content.represent(article, viewer(conn))

    conn |> put_status(409) |> json(%{errors: %{revision: ["is stale"]}, article: current})
  end

  defp reply(conn, {:error, %Ecto.Changeset{} = c}, _, _, _),
    do: error(conn, 422, Ecto.Changeset.traverse_errors(c, fn {msg, _} -> msg end))

  defp reply(conn, {:error, errors}, _, _, _), do: error(conn, 422, errors)
  defp reply(conn, {:conflict, errors}, _, _, _), do: error(conn, 409, errors)
  defp reply(conn, {:unauthorized, errors}, _, _, _), do: error(conn, 401, errors)
  defp reply(conn, {:limited, errors}, _, _, _), do: error(conn, 429, errors)
  defp reply(conn, {:not_found, field}, _, _, _), do: error(conn, 404, %{field => ["not found"]})
  defp reply(conn, {:forbidden, field}, _, _, _), do: error(conn, 403, %{field => ["forbidden"]})
  defp error(conn, status, errors), do: conn |> put_status(status) |> json(%{errors: errors})
end

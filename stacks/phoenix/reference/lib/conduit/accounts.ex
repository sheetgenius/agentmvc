defmodule Conduit.Accounts do
  import Ecto.Query
  alias Conduit.{Repo, User}

  def register(attrs) when is_map(attrs) do
    %User{} |> User.changeset(attrs, true) |> Repo.insert() |> duplicate()
  end

  def register(_), do: {:error, %{user: ["is invalid"]}}

  def update(%User{} = user, attrs) when is_map(attrs) do
    user |> User.changeset(attrs) |> Repo.update() |> duplicate()
  end

  def update(_, _), do: {:error, %{user: ["is invalid"]}}

  def login(attrs) when is_map(attrs) do
    email = attrs["email"]
    password = attrs["password"]

    cond do
      not is_binary(email) or email == "" ->
        {:error, %{email: ["can't be blank"]}}

      not is_binary(password) or password == "" ->
        {:error, %{password: ["can't be blank"]}}

      true ->
        user = Repo.get_by(User, email: email)

        if User.password_valid?(user, password),
          do: {:ok, user},
          else: {:unauthorized, %{credentials: ["invalid"]}}
    end
  end

  def login(_), do: {:error, %{credentials: ["invalid"]}}

  def token(user), do: Phoenix.Token.sign(ConduitWeb.Endpoint, "user", user.id)

  def by_token(token) do
    with {:ok, id} <-
           Phoenix.Token.verify(ConduitWeb.Endpoint, "user", token, max_age: 60 * 60 * 24 * 365),
         %User{} = user <- Repo.get(User, id),
         do: user,
         else: (_ -> nil)
  end

  def profile(username, viewer) do
    case Repo.get_by(User, username: username) do
      nil ->
        {:not_found, :profile}

      user ->
        {:ok,
         %{
           username: user.username,
           bio: user.bio,
           image: user.image,
           following: following?(viewer, user)
         }}
    end
  end

  def follow(viewer, username, follow?) do
    with {:ok, user} <- profile_user(username) do
      if follow? do
        Repo.insert_all("follows", [%{follower_id: viewer.id, followed_id: user.id}],
          on_conflict: :nothing
        )
      else
        Repo.delete_all(
          from f in "follows", where: f.follower_id == ^viewer.id and f.followed_id == ^user.id
        )
      end

      profile(username, viewer)
    end
  end

  def following?(nil, _), do: false

  def following?(viewer, user) do
    Repo.exists?(
      from f in "follows", where: f.follower_id == ^viewer.id and f.followed_id == ^user.id
    )
  end

  defp profile_user(username) do
    case Repo.get_by(User, username: username),
      do: (
        nil -> {:not_found, :profile}
        user -> {:ok, user}
      )
  end

  defp duplicate({:error, %Ecto.Changeset{} = c}) do
    errors = Ecto.Changeset.traverse_errors(c, fn {msg, _} -> msg end)

    if Enum.any?(Map.values(errors), &Enum.member?(&1, "has already been taken")),
      do: {:conflict, errors},
      else: {:error, errors}
  end

  defp duplicate(result), do: result
end

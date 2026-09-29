defmodule Conduit.Accounts do
  import Ecto.Query
  alias Conduit.Repo
  alias Conduit.Accounts.LoginLimiter
  alias Conduit.Accounts.User

  defp claims, do: Joken.Config.default_claims(default_exp: 60 * 60 * 24 * 30)

  def register(attrs), do: %User{} |> User.changeset(attrs, true) |> Repo.insert()
  def update(user, attrs), do: user |> User.changeset(attrs) |> Repo.update()

  def login(attrs) when is_map(attrs) do
    missing = Enum.find(["email", "password"], &(not is_binary(attrs[&1]) or attrs[&1] == ""))

    cond do
      missing -> {:error, {:validation, %{missing => ["can't be blank"]}}}
      not LoginLimiter.allowed?(attrs["email"]) -> {:error, :rate_limited}
      true -> check_login(attrs)
    end
  end

  def login(_), do: {:error, {:validation, %{"user" => ["is invalid"]}}}

  defp check_login(attrs) do
    user = Repo.get_by(User, email: attrs["email"])

    valid =
      Bcrypt.verify_pass(
        attrs["password"],
        (user && user.password_hash) || LoginLimiter.dummy_hash()
      )

    if user && valid do
      LoginLimiter.clear(attrs["email"])
      {:ok, user}
    else
      LoginLimiter.failed(attrs["email"])
      {:error, :credentials}
    end
  end

  def token(user) do
    signer = Joken.Signer.create("HS256", signing_secret())

    {:ok, token, _} =
      Joken.generate_and_sign(claims(), %{"sub" => Integer.to_string(user.id)}, signer)

    token
  end

  def caller(nil), do: :anonymous

  def caller("Token " <> token) do
    signer = Joken.Signer.create("HS256", signing_secret())

    with {:ok, %{"sub" => id}} <- Joken.verify_and_validate(claims(), token, signer),
         {id, ""} <- Integer.parse(id),
         %User{} = user <- Repo.get(User, id) do
      {:user, user}
    else
      _ -> :invalid
    end
  end

  def caller(_), do: :invalid

  def require_user({:user, user}), do: {:ok, user}
  def require_user(:anonymous), do: {:error, {:token, "is missing"}}
  def require_user(:invalid), do: {:error, {:token, "is invalid"}}

  def profile(user, caller) do
    following =
      case caller do
        {:user, viewer} ->
          Repo.exists?(
            from f in "follows", where: f.follower_id == ^viewer.id and f.followed_id == ^user.id
          )

        _ ->
          false
      end

    %{username: user.username, bio: user.bio, image: user.image, following: following}
  end

  def find_profile(username),
    do: Repo.get_by(User, username: username) || {:error, {:profile, "not found"}}

  def follow(viewer, target, following?) do
    if viewer.id != target.id do
      if following? do
        Repo.insert_all("follows", [%{follower_id: viewer.id, followed_id: target.id}],
          on_conflict: :nothing
        )
      else
        Repo.delete_all(
          from f in "follows", where: f.follower_id == ^viewer.id and f.followed_id == ^target.id
        )
      end
    end

    profile(target, {:user, viewer})
  end

  defp signing_secret, do: ConduitWeb.Endpoint.config(:secret_key_base)
end

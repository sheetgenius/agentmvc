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

  def following?(nil, _profile), do: false

  def following?(_viewer, %User{followed_by_viewer: followed}) when is_boolean(followed),
    do: followed

  def following?(viewer, profile) do
    Repo.exists?(from u in Ecto.assoc(viewer, :following), where: u.id == ^profile.id)
  end

  def follow(viewer, profile) do
    Repo.insert_all("follows", [%{follower_id: viewer.id, followed_id: profile.id}],
      on_conflict: :nothing
    )

    :ok
  end

  def unfollow(viewer, profile) do
    Repo.delete_all(
      from f in "follows", where: f.follower_id == ^viewer.id and f.followed_id == ^profile.id
    )

    :ok
  end

  defp signer, do: Joken.Signer.create("HS256", ConduitWeb.Endpoint.config(:secret_key_base))
  defp token_claims, do: Joken.Config.default_claims(skip: [:iss, :aud, :jti])
end

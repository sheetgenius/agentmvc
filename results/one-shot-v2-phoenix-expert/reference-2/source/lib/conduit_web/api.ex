defmodule ConduitWeb.API do
  import Plug.Conn
  alias Conduit.Accounts

  def caller(conn), do: conn.assigns.caller
  def user(conn), do: Accounts.require_user(caller(conn))

  def reply(conn, status, body), do: Phoenix.Controller.json(put_status(conn, status), body)
  def no_content(conn), do: send_resp(conn, 204, "")

  def result(conn, {:ok, value}, status, render), do: reply(conn, status, render.(value))
  def result(conn, {:error, reason}, _status, _render), do: error(conn, reason)

  def error(conn, %Ecto.Changeset{} = changeset) do
    errors =
      Ecto.Changeset.traverse_errors(changeset, fn {message, opts} ->
        Enum.reduce(opts, message, fn {key, value}, acc ->
          String.replace(acc, "%{#{key}}", if(is_binary(value), do: value, else: inspect(value)))
        end)
      end)

    status =
      if Enum.any?(errors, fn {_key, messages} -> "has already been taken" in messages end),
        do: 409,
        else: 422

    reply(conn, status, %{errors: errors})
  end

  def error(conn, {:validation, errors}), do: reply(conn, 422, %{errors: errors})

  def error(conn, {:stale, article}) do
    reply(conn, 409, %{
      errors: %{revision: ["is stale"]},
      article: Conduit.Articles.present_one(article, caller(conn))
    })
  end

  def error(conn, {:stale_shared, article}) do
    reply(conn, 409, %{
      errors: %{revision: ["is stale"]},
      article: Conduit.Articles.shared(article)
    })
  end

  def error(conn, {field, message}) when is_atom(field) and is_binary(message) do
    status =
      case {field, message} do
        {:token, _} -> 401
        {:credentials, _} -> 401
        {_, "not found"} -> 404
        {_, "forbidden"} -> 403
        _ -> 422
      end

    reply(conn, status, %{errors: %{field => [message]}})
  end

  def error(conn, :credentials), do: error(conn, {:credentials, "invalid"})

  def error(conn, :rate_limited),
    do: reply(conn, 429, %{errors: %{credentials: ["rate limited"]}})

  def error(conn, _), do: reply(conn, 422, %{errors: %{request: ["is invalid"]}})

  def object(params, key) do
    case Map.get(params, key) do
      value when is_map(value) -> {:ok, value}
      _ -> {:error, {:validation, %{key => ["is invalid"]}}}
    end
  end
end

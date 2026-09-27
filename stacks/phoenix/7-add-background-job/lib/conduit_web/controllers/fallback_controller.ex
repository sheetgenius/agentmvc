defmodule ConduitWeb.FallbackController do
  use ConduitWeb, :controller

  def call(conn, {:error, %Ecto.Changeset{} = changeset}) do
    errors =
      changeset
      |> Ecto.Changeset.traverse_errors(fn {message, opts} ->
        Enum.reduce(opts, message, fn {key, value}, text ->
          String.replace(text, "%{#{key}}", fn _ -> to_string(value) end)
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

  def call(conn, {:draft, resource}),
    do: error(conn, :unprocessable_entity, resource, "is a draft")

  def call(conn, {:blank, field}), do: error(conn, :unprocessable_entity, field, "can't be blank")
  def call(conn, {:invalid, field}), do: error(conn, :unprocessable_entity, field, "is invalid")

  def call(conn, {:rate_limited, retry_after}) do
    conn
    |> put_resp_header("retry-after", Integer.to_string(ceil(retry_after / 1000)))
    |> error(:too_many_requests, :credentials, "too many attempts")
  end

  defp error(conn, status, field, message),
    do: conn |> put_status(status) |> json(%{errors: %{field => [message]}})

  defp error_field(:tag_list), do: "tagList"
  defp error_field(field), do: field
end

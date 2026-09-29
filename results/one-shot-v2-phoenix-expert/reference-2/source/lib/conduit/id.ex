defmodule Conduit.Id do
  @moduledoc false
  @max 9_223_372_036_854_775_807

  def parse(value) when is_binary(value) do
    case Integer.parse(value) do
      {id, ""} when id > 0 and id <= @max -> {:ok, id}
      _ -> :error
    end
  end

  def parse(_), do: :error
end

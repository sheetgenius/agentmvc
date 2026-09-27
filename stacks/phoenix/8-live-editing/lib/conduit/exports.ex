defmodule Conduit.Exports do
  import Ecto.Query
  alias Conduit.Content.Article
  alias Conduit.Exports.{Export, Worker}
  alias Conduit.Repo

  def create(user) do
    Ecto.Multi.new()
    |> Ecto.Multi.insert(:export, %Export{user_id: user.id})
    |> Oban.insert(:job, fn %{export: export} -> Worker.new(%{export_id: export.id}) end)
    |> Repo.transaction()
    |> case do
      {:ok, %{export: export}} -> {:ok, export}
      {:error, _step, reason, _changes} -> {:error, reason}
    end
  end

  def get(user, id) do
    case Integer.parse(id) do
      {id, ""} when id > 0 and id <= 9_223_372_036_854_775_807 ->
        case Repo.get_by(Export, id: id, user_id: user.id) do
          nil -> {:error, :export}
          export -> {:ok, export}
        end

      _ ->
        {:error, :export}
    end
  end

  def complete(id) do
    case Repo.get(Export, id) do
      nil ->
        :ok

      %Export{status: :done} ->
        :ok

      export ->
        articles =
          from(a in Article,
            where: a.author_id == ^export.user_id,
            left_join: c in assoc(a, :comments),
            group_by: a.id,
            order_by: [asc: a.inserted_at, asc: a.id],
            select: %{
              slug: a.slug,
              title: a.title,
              description: a.description,
              body: a.body,
              tagList: a.tag_list,
              status: a.status,
              commentsCount: count(c.id)
            }
          )
          |> Repo.all()

        export
        |> Ecto.Changeset.change(
          status: :done,
          articles: articles,
          completed_at: DateTime.utc_now()
        )
        |> Repo.update!()

        :ok
    end
  end
end

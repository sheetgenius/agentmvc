defmodule Conduit.Exports do
  import Ecto.Query
  alias Conduit.Repo
  alias Conduit.Exports.Export
  alias Conduit.Articles.Article

  def start(user) do
    Ecto.Multi.new()
    |> Ecto.Multi.insert(:export, %Export{user_id: user.id})
    |> Ecto.Multi.run(:job, fn _repo, %{export: export} ->
      Oban.insert(Conduit.Exports.Worker.new(%{export_id: export.id}))
    end)
    |> Repo.transaction()
    |> case do
      {:ok, %{export: export}} -> {:ok, export}
      {:error, _, reason, _} -> {:error, reason}
    end
  end

  def get(user, id) when is_binary(id) do
    case Integer.parse(id) do
      {number, ""} ->
        case Repo.get_by(Export, id: number, user_id: user.id) do
          nil -> missing()
          export -> {:ok, export}
        end

      _ ->
        missing()
    end
  end

  def render(export) do
    %{
      id: export.id,
      status: export.status,
      createdAt: DateTime.to_iso8601(export.inserted_at),
      completedAt: if(export.completed_at, do: DateTime.to_iso8601(export.completed_at)),
      articles: export.articles
    }
  end

  def complete(id) do
    Repo.transaction(fn ->
      export = Repo.one!(from e in Export, where: e.id == ^id, lock: "FOR UPDATE")

      if export.status == "pending" do
        articles =
          Repo.all(
            from a in Article,
              where: a.author_id == ^export.user_id,
              order_by: [asc: a.inserted_at, asc: a.id],
              select: %{
                id: a.id,
                slug: a.slug,
                title: a.title,
                description: a.description,
                body: a.body,
                tagList: a.tag_list,
                status: a.status
              }
          )

        ids = Enum.map(articles, & &1.id)

        counts =
          Repo.all(
            from c in "comments",
              where: c.article_id in ^ids,
              group_by: c.article_id,
              select: {c.article_id, count(c.id)}
          )
          |> Map.new()

        snapshot =
          Enum.map(articles, fn a ->
            a |> Map.delete(:id) |> Map.put(:commentsCount, Map.get(counts, a.id, 0))
          end)

        export
        |> Ecto.Changeset.change(
          status: "done",
          articles: snapshot,
          completed_at: DateTime.utc_now()
        )
        |> Repo.update!()
      end
    end)
  end

  defp missing, do: {:error, {:export, "not found"}}
end

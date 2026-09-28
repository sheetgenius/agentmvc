defmodule Conduit.Exports do
  import Ecto.Query
  alias Conduit.{Repo, Export, Article}

  def create(user) do
    with {:ok, export} <- Repo.insert(%Export{user_id: user.id}),
         {:ok, _job} <- %{export_id: export.id} |> Conduit.ExportWorker.new() |> Oban.insert() do
      {:ok, export}
    end
  end

  def get(user, id) do
    case Integer.parse(id) do
      {id, ""} ->
        case Repo.get_by(Export, id: id, user_id: user.id) do
          nil -> {:not_found, :export}
          export -> {:ok, export}
        end

      _ ->
        {:not_found, :export}
    end
  end

  def run(id) do
    export = Repo.get!(Export, id)

    articles =
      Repo.all(
        from a in Article,
          where: a.author_id == ^export.user_id,
          order_by: [asc: a.inserted_at, asc: a.id]
      )

    snapshot =
      Enum.map(articles, fn a ->
        %{
          slug: a.slug,
          title: a.title,
          description: a.description,
          body: a.body,
          tagList: a.tag_list,
          status: a.status,
          commentsCount:
            Repo.aggregate(from(c in Conduit.Comment, where: c.article_id == ^a.id), :count, :id)
        }
      end)

    export
    |> Ecto.Changeset.change(
      status: "done",
      articles: %{"items" => snapshot},
      completed_at: DateTime.utc_now()
    )
    |> Repo.update!()
  end

  def represent(export),
    do: %{
      id: export.id,
      status: export.status,
      createdAt: export.inserted_at,
      completedAt: export.completed_at,
      articles: if(export.articles, do: export.articles["items"], else: nil)
    }
end

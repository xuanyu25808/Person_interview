from app.services.retrieval import retrieve_documents


def test_retrieval_ranks_matching_markdown_documents() -> None:
    results = retrieve_documents("retrieval ranking and search projects")

    assert results
    assert results[0].slug == "projects"
    assert all(result.source_path.name.endswith(".md") for result in results)

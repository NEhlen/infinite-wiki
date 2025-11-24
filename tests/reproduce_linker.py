import sys
import os
from unittest.mock import MagicMock

# Add app to path
sys.path.append(os.getcwd())

from app.core.linker import linker_service
from app.core.graph import graph_service
from app.models.article import Article


def test_linker():
    world_name = "test_world"

    # 1. Setup Graph with one existing and one missing entity
    graph = graph_service.get_graph(world_name)
    graph.add_node("Existing Article")
    graph.add_node("Missing Article")

    # 2. Mock Session
    mock_session = MagicMock()

    # Mock exec().first() behavior
    def mock_exec(statement):
        # Extract the title from the statement (this is a bit hacky but works for simple selects)
        # In SQLModel, statement is a SelectOfScalar.
        # We can't easily inspect it without compiling.
        # So let's mock the side effect based on the call arguments?
        # No, that's hard.

        # Alternative: We can mock the session.exec return value to be a mock object
        # whose .first() method returns based on some external state?
        pass

    # Let's just mock the return value of session.exec
    # The linker calls: session.exec(statement).first()

    # We need to intercept the call.
    # Since we can't easily inspect the statement object in the mock,
    # let's monkeypatch the linker's internal logic or just trust the mock?

    # Actually, let's use a real in-memory SQLite DB for the session to be accurate.
    from sqlmodel import create_engine, SQLModel, Session

    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        # Add "Existing Article" to DB
        article = Article(title="Existing Article", content="Foo", summary="Bar")
        session.add(article)
        session.commit()

        # 3. Run Linker
        content = "Here is a link to Existing Article and one to Missing Article."
        linked = linker_service.autolink_content(world_name, content, session)

        print(f"Original: {content}")
        print(f"Linked:   {linked}")

        # 4. Verify
        if "[Existing Article](/world/test_world/wiki/Existing%20Article)" in linked:
            print("PASS: Existing Article linked correctly (Blue).")
        else:
            print("FAIL: Existing Article NOT linked correctly.")

        if 'class="new-article"' in linked and "Missing Article" in linked:
            print("PASS: Missing Article linked correctly (Red).")
        else:
            print(
                "FAIL: Missing Article NOT linked correctly (Expected class='new-article')."
            )


if __name__ == "__main__":
    test_linker()

import arangomapper


def test_imports():
    assert hasattr(arangomapper, "AQLManager")
    assert hasattr(arangomapper, "AsyncAQLManager")
    assert hasattr(arangomapper, "For")
    assert hasattr(arangomapper, "ForGraph")
    assert hasattr(arangomapper, "Let")
    assert hasattr(arangomapper, "Raw")
    assert hasattr(arangomapper, "GraphResponse")
    assert hasattr(arangomapper, "PathResponse")
    assert hasattr(arangomapper, "AsyncConn")
    assert hasattr(arangomapper, "AsyncCollectionManager")
    assert hasattr(arangomapper, "get_db")
    assert hasattr(arangomapper, "CollectionManager")
    assert hasattr(arangomapper, "CollectionBase")
    assert hasattr(arangomapper, "CollectionEdge")

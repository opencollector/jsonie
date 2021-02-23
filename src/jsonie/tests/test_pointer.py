def test_jsonpointer_init_with_str():
    from ..pointer import JSONPointer

    assert str(JSONPointer("/")) == "/"
    assert str(JSONPointer("/a/b/c/0")) == "/a/b/c/0"
    assert str(JSONPointer("a/b/c/0")) == "/a/b/c/0"


def test_jsonpointer_init_with_int():
    from ..pointer import JSONPointer

    assert str(JSONPointer([])) == "/"
    assert str(JSONPointer(["a", "b", "c", "0"])) == "/a/b/c/0"
    assert str(JSONPointer(["a", "b", "c", 0])) == "/a/b/c/0"

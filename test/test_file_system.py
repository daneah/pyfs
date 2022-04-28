import pytest

from pyfs import FileSystem, NoSuchFileOrDirectory, NotADirectory, IsADirectory, FileExists


@pytest.fixture
def fs():
    return FileSystem()


def test_file_system_starts_in_root_directory(fs):
    assert fs.cwd() == "/"


def test_removing_nonexistent_file_raises_exception(fs):
    with pytest.raises(NoSuchFileOrDirectory):
        fs.rm("i-dont-exist")


def test_changing_to_nonexistent_directory_raises_exception(fs):
    with pytest.raises(NoSuchFileOrDirectory):
        fs.cd("i-dont-exist")


def test_changing_up_a_directory_at_root_is_noop(fs):
    fs.cd("..")
    fs.cd("..")
    fs.cd("..")
    assert fs.cwd() == "/"


def test_cannot_cd_to_regular_file(fs):
    fs.touch("test.txt")
    with pytest.raises(NotADirectory):
        fs.cd("test.txt")


def test_cd_is_atomic(fs):
    fs.mkdir("one")
    fs.mkdir("two")
    fs.cd("one")
    with pytest.raises(NoSuchFileOrDirectory):
        fs.cd("../three")
    assert fs.cwd() == "/one"


def test_cannot_remove_directory_without_recursive(fs):
    fs.mkdir("test")
    with pytest.raises(IsADirectory):
        fs.rm("test")


def test_cannot_create_existing_directory(fs):
    fs.mkdir("test")
    with pytest.raises(FileExists):
        fs.mkdir("test")


def test_make_directory_with_missing_parent(fs):
    with pytest.raises(NoSuchFileOrDirectory):
        fs.mkdir("one/two")


def test_make_directory_with_intermediates(fs):
    fs.mkdir("one/two", create_intermediates=True)
    assert fs.ls() == ["one"]
    fs.cd("one")
    assert fs.ls() == ["two"]


def test_cannot_create_existing_file(fs):
    first_file_node = fs.touch("test.txt")
    second_file_node = fs.touch("test.txt")
    assert second_file_node is first_file_node


def test_directories_in_different_locations_with_same_name(fs):
    fs.mkdir("cats")
    fs.mkdir("dogs")
    fs.cd("dogs")
    fs.mkdir("pets")
    fs.cd("..")
    fs.cd("cats")
    fs.mkdir("pets")
    assert fs.ls() == ["pets"]
    fs.cd("pets")
    assert fs.cwd() == "/cats/pets"


def test_end_to_end(fs):
    fs.mkdir("school")
    fs.cd("school")
    assert fs.cwd() == "/school"
    fs.mkdir("homework")
    fs.cd("homework")
    fs.mkdir("math")
    fs.mkdir("lunch")
    fs.mkdir("history")
    fs.mkdir("spanish")
    fs.rm("lunch", recursive=True)
    assert fs.ls() == ["math", "history", "spanish"]
    assert fs.cwd() == "/school/homework"
    fs.cd("..")
    fs.mkdir("cheatsheet")
    assert fs.ls() == ["homework", "cheatsheet"]
    fs.rm("cheatsheet", recursive=True)
    fs.cd("..")
    assert fs.cwd() == "/"


def test_write_to_file_can_be_read(fs):
    fs.touch("test.txt")
    fs.write_file("test.txt", "Hello, world!")
    assert fs.read_file("test.txt") == "Hello, world!"


def test_reading_a_nonexistent_file_raises_exception(fs):
    with pytest.raises(NoSuchFileOrDirectory):
        fs.read_file("i-dont-exist.txt")


def test_reading_a_directory_raises_exception(fs):
    fs.mkdir("test")
    with pytest.raises(IsADirectory):
        fs.read_file("test")


def test_can_nest_many_directories(fs):
    for i in range(1_000):
        fs.mkdir("foo")
        fs.cd("foo")
    assert fs.cwd() == "/foo" * 1_000


def test_can_create_many_files(fs):
    for i in range(1_000):
        fs.touch(f"test-{i}.txt")


def test_moving_file(fs):
    fs.touch("old.txt")
    fs.mv("old.txt", "new.txt")
    assert fs.ls() == ["new.txt"]


def test_moving_nonexistent_file_raises_exception(fs):
    with pytest.raises(NoSuchFileOrDirectory):
        fs.mv("i-dont-exist", "i-still-dont-exist")


def test_find(fs):
    fs.mkdir("a")
    fs.cd("a")
    fs.mkdir("b")
    fs.cd("b")
    fs.mkdir("c")
    fs.cd("c")
    fs.mkdir("d")
    fs.cd("d")
    fs.touch("e")
    fs.cd("..")
    fs.cd("..")
    fs.mkdir("e")
    fs.cd("..")
    fs.cd("..")
    assert fs.find("e") == ["a/b/e", "a/b/c/d/e"]


def test_find_when_not_at_root(fs):
    fs.mkdir("one/two", create_intermediates=True)
    fs.cd("one")
    assert fs.find("two") == ["two"]


def test_find_relative(fs):
    fs.mkdir("one/two/three", create_intermediates=True)
    fs.cd("one/two")
    assert fs.find("three", "/one") == ["/one/two/three"]


def test_find_is_limited_to_tree_under_current_directory(fs):
    fs.mkdir("one")
    fs.cd("one")
    fs.mkdir("two")
    fs.cd("..")
    fs.mkdir("three")
    fs.cd("three")
    assert fs.find("two") == []


def test_hard_link(fs):
    fs.mkdir("one")
    fs.cd("one")
    target = fs.touch("target.txt")
    fs.write_file("target.txt", "This is written in the target")
    dest = fs.ln("target.txt", "dest.txt")
    assert dest is target
    assert fs.read_file("dest.txt") == "This is written in the target"
    fs.cd("..")
    fs.ln("one", "two")
    fs.cd("two")
    assert fs.ls() == ["target.txt", "dest.txt"]


def test_stream_from_file(fs):
    fs.touch("big-one.txt")
    fs.write_file("big-one.txt", "0" * 1_000)
    for byte in fs.read_file("big-one.txt", stream=True):
        assert byte == "0"


def test_cd_without_arguments_goes_to_root(fs):
    fs.mkdir("one")
    fs.cd("one")
    fs.mkdir("two")
    fs.cd("two")
    fs.cd()
    assert fs.cwd() == "/"


def test_relative_paths(fs):
    fs.mkdir("one/two/three", create_intermediates=True)
    fs.cd("one/two")
    fs.cd("./three")
    fs.cd("/one/two")
    fs.mkdir("../four")
    fs.cd("../four")
    assert fs.cwd() == "/one/four"
    fs.touch("/one/two/file.txt")
    fs.write_file("/one/two/file.txt", "hello!")
    assert fs.ls("/one/two") == ["three", "file.txt"]
    fs.cd("/one/two")
    assert fs.read_file("./file.txt") == "hello!"
    fs.mv("file.txt", "/one/two/file.txt")
    fs.ln("/one/two/file.txt", "/one/two/three/file.txt")
    assert fs.read_file("/one/two/file.txt") == "hello!"
    fs.rm("/one/two/file.txt")
    assert fs.ls("/one/two") == ["three"]
    assert fs.ls("/one/two/three") == ["file.txt"]
    assert fs.read_file("/one/two/three/file.txt") == "hello!"

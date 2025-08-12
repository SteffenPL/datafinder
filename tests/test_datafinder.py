import pytest
import tempfile
import shutil
import os
from pathlib import Path
from datafinder.datafinder import DataFinder

@pytest.fixture(scope="function")
def temp_dir():
    test_dir = tempfile.mkdtemp()
    sub_dir = os.path.join(test_dir, "sub")
    os.makedirs(sub_dir)
    file1 = os.path.join(sub_dir, "ABC123_type.tif")
    file2 = os.path.join(sub_dir, "DEF456_other.tif")
    with open(file1, "w") as f:
        f.write("test")
    with open(file2, "w") as f:
        f.write("test2")
    yield test_dir, sub_dir, file1, file2
    shutil.rmtree(test_dir)

def test_init_and_add_folders(temp_dir):
    test_dir, sub_dir, _, _ = temp_dir
    df = DataFinder([sub_dir], root=test_dir)
    assert len(df.folders) == 1
    assert Path(df.folders[0]).is_dir()

def test_add_nonexistent_folder(temp_dir):
    test_dir, _, _, _ = temp_dir
    df = DataFinder([], root=test_dir)
    with pytest.raises(ValueError):
        df.add_folders(["does_not_exist"], strict=True)

def test_query_with_regex(temp_dir):
    test_dir, sub_dir, _, _ = temp_dir
    df = DataFinder([sub_dir], root=test_dir)
    regex_info = {0: r"(?P<condition>\w{3})(?P<id>\d{3})_(?P<type>\w*).tif"}
    result = df.query("*.tif", regex_info=regex_info)
    assert len(result) == 2
    assert "condition" in result.columns
    assert "id" in result.columns
    assert "type" in result.columns
    assert (result["condition"] == "ABC").any()
    assert (result["condition"] == "DEF").any()

def test_query_require_match_false(temp_dir):
    test_dir, sub_dir, _, _ = temp_dir
    df = DataFinder([sub_dir], root=test_dir)
    regex_info = {0: r"(?P<condition>XXX)(?P<id>\d{3})_(?P<type>\w*).tif"}
    result = df.query("*.tif", regex_info=regex_info, require_match=False)
    assert len(result) == 2  # Both files should be kept

from pathlib import Path
import pytest

@pytest.fixture(scope="package", params=(Path(__file__).parent / "data").iterdir())
def test_data_path(request):
    """
    Return all data test cases under the "data" folder
    """
    return request.param

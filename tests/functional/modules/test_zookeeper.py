import pytest

pytestmark = [
    pytest.mark.requires_salt_modules("zookeeper.example_function"),
]


@pytest.fixture
def zookeeper(modules):
    return modules.zookeeper


def test_replace_this_this_with_something_meaningful(zookeeper):
    echo_str = "Echoed!"
    res = zookeeper.example_function(echo_str)
    assert res == echo_str

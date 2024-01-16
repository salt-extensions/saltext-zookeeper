import pytest

pytestmark = [
    pytest.mark.requires_salt_states("zookeeper.exampled"),
]


@pytest.fixture
def zookeeper(states):
    return states.zookeeper


def test_replace_this_this_with_something_meaningful(zookeeper):
    echo_str = "Echoed!"
    ret = zookeeper.exampled(echo_str)
    assert ret.result
    assert not ret.changes
    assert echo_str in ret.comment

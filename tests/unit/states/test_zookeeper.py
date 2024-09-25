import pytest
import salt.modules.test as testmod

import saltext.zookeeper.modules.zookeeper_mod as zookeeper_module
import saltext.zookeeper.states.zookeeper_mod as zookeeper_state


@pytest.fixture
def configure_loader_modules():
    return {
        zookeeper_module: {
            "__salt__": {
                "test.echo": testmod.echo,
            },
        },
        zookeeper_state: {
            "__salt__": {
                "zookeeper.example_function": zookeeper_module.example_function,
            },
        },
    }


def test_replace_this_this_with_something_meaningful():
    echo_str = "Echoed!"
    expected = {
        "name": echo_str,
        "changes": {},
        "result": True,
        "comment": f"The 'zookeeper.example_function' returned: '{echo_str}'",
    }
    assert zookeeper_state.exampled(echo_str) == expected

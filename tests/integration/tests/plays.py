# Handle integration tests
from typing import Union, Dict, List, Any
from utils import get_last_trace, parse_and_validate_trace
from event import HostEvent
import pytest

JSONTYPE = Union[None, int, str, bool, List[Any], Dict[str, Any]]


@pytest.mark.ansible_playbook('plays/base.yml')
@pytest.mark.ansible_inventory('inventories/multiple_hosts.ini')
@pytest.mark.ansible_strategy('free')
def test_basic_multiple_free(ansible_play):
    trace_hosts: Dict[int, HostEvent]
    trace_events: Dict[int, Any]
    trace_json: JSONTYPE = get_last_trace()
    trace_hosts, trace_events = parse_and_validate_trace(trace_json)


@pytest.mark.ansible_playbook('plays/base.yml')
@pytest.mark.ansible_inventory('inventories/multiple_hosts.ini')
@pytest.mark.ansible_strategy('linear')
def test_basic_multiple_linear(ansible_play):
    trace_hosts: Dict[int, HostEvent]
    trace_events: Dict[int, Any]
    trace_json: JSONTYPE = get_last_trace()
    trace_hosts, trace_events = parse_and_validate_trace(trace_json)


@pytest.mark.ansible_playbook('plays/base.yml')
@pytest.mark.ansible_inventory('inventories/one_host.ini')
@pytest.mark.ansible_strategy('linear')
def test_basic_single_linear(ansible_play):
    trace_hosts: Dict[int, HostEvent]
    trace_events: Dict[int, Any]
    trace_json: JSONTYPE = get_last_trace()
    trace_hosts, trace_events = parse_and_validate_trace(trace_json)

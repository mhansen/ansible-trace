# Handle integration tests
from typing import Union, Dict, List, Any
from utils import get_last_trace, parse_and_validate_trace
from event import HostEvent
import pytest

JSONTYPE = Union[None, int, str, bool, List[Any], Dict[str, Any]]


@pytest.mark.ansible_playbook('roles/base.yml')
@pytest.mark.ansible_inventory('inventories/multiple_hosts.ini')
@pytest.mark.ansible_strategy('free')
def test_base_multiple_free(ansible_play):
    trace_hosts: Dict[int, HostEvent]
    trace_events: Dict[int, List[List[Any]]]
    trace_json: JSONTYPE = get_last_trace()
    trace_hosts, trace_events = parse_and_validate_trace(trace_json)


@pytest.mark.ansible_playbook('roles/base.yml')
@pytest.mark.ansible_inventory('inventories/multiple_hosts.ini')
@pytest.mark.ansible_strategy('linear')
def test_base_multiple_linear(ansible_play):
    trace_hosts: Dict[int, HostEvent]
    trace_events: Dict[int, List[List[Any]]]
    trace_json: JSONTYPE = get_last_trace()
    trace_hosts, trace_events = parse_and_validate_trace(trace_json)


@pytest.mark.ansible_playbook('roles/base.yml')
@pytest.mark.ansible_inventory('inventories/one_host.ini')
@pytest.mark.ansible_strategy('linear')
def test_base_single_linear(ansible_play):
    trace_hosts: Dict[int, HostEvent]
    trace_events: Dict[int, List[List[Any]]]
    trace_json: JSONTYPE = get_last_trace()
    trace_hosts, trace_events = parse_and_validate_trace(trace_json)


@pytest.mark.ansible_playbook('roles/one_import_role.yml')
@pytest.mark.ansible_inventory('inventories/multiple_hosts.ini')
@pytest.mark.ansible_strategy('free')
def test_import_multiple_free(ansible_play):
    trace_hosts: Dict[int, HostEvent]
    trace_events: Dict[int, List[List[Any]]]
    trace_json: JSONTYPE = get_last_trace()
    trace_hosts, trace_events = parse_and_validate_trace(trace_json)


@pytest.mark.ansible_playbook('roles/one_import_role.yml')
@pytest.mark.ansible_inventory('inventories/multiple_hosts.ini')
@pytest.mark.ansible_strategy('linear')
def test_import_multiple_linear(ansible_play):
    trace_hosts: Dict[int, HostEvent]
    trace_events: Dict[int, List[List[Any]]]
    trace_json: JSONTYPE = get_last_trace()
    trace_hosts, trace_events = parse_and_validate_trace(trace_json)


@pytest.mark.ansible_playbook('roles/one_import_role.yml')
@pytest.mark.ansible_inventory('inventories/one_host.ini')
@pytest.mark.ansible_strategy('linear')
def test_import_single_linear(ansible_play):
    trace_hosts: Dict[int, HostEvent]
    trace_events: Dict[int, List[List[Any]]]
    trace_json: JSONTYPE = get_last_trace()
    trace_hosts, trace_events = parse_and_validate_trace(trace_json)


@pytest.mark.ansible_playbook('roles/no_task_at_end.yml')
@pytest.mark.ansible_inventory('inventories/multiple_hosts.ini')
@pytest.mark.ansible_strategy('free')
def test_edge_end_multiple_free(ansible_play):
    trace_hosts: Dict[int, HostEvent]
    trace_events: Dict[int, List[List[Any]]]
    trace_json: JSONTYPE = get_last_trace()
    trace_hosts, trace_events = parse_and_validate_trace(trace_json)


@pytest.mark.ansible_playbook('roles/no_task_at_end.yml')
@pytest.mark.ansible_inventory('inventories/multiple_hosts.ini')
@pytest.mark.ansible_strategy('linear')
def test_edge_end_multiple_linear(ansible_play):
    trace_hosts: Dict[int, HostEvent]
    trace_events: Dict[int, List[List[Any]]]
    trace_json: JSONTYPE = get_last_trace()
    trace_hosts, trace_events = parse_and_validate_trace(trace_json)


@pytest.mark.ansible_playbook('roles/no_task_at_end.yml')
@pytest.mark.ansible_inventory('inventories/one_host.ini')
@pytest.mark.ansible_strategy('linear')
def test_edge_end_single_linear(ansible_play):
    trace_hosts: Dict[int, HostEvent]
    trace_events: Dict[int, List[List[Any]]]
    trace_json: JSONTYPE = get_last_trace()
    trace_hosts, trace_events = parse_and_validate_trace(trace_json)


@pytest.mark.ansible_playbook('roles/complete.yml')
@pytest.mark.ansible_inventory('inventories/multiple_hosts.ini')
@pytest.mark.ansible_strategy('free')
def test_complete_multiple_free(ansible_play):
    trace_hosts: Dict[int, HostEvent]
    trace_events: Dict[int, List[List[Any]]]
    trace_json: JSONTYPE = get_last_trace()
    trace_hosts, trace_events = parse_and_validate_trace(trace_json)


@pytest.mark.ansible_playbook('roles/complete.yml')
@pytest.mark.ansible_inventory('inventories/multiple_hosts.ini')
@pytest.mark.ansible_strategy('linear')
def test_complete_multiple_linear(ansible_play):
    trace_hosts: Dict[int, HostEvent]
    trace_events: Dict[int, List[List[Any]]]
    trace_json: JSONTYPE = get_last_trace()
    trace_hosts, trace_events = parse_and_validate_trace(trace_json)


@pytest.mark.ansible_playbook('roles/complete.yml')
@pytest.mark.ansible_inventory('inventories/one_host.ini')
@pytest.mark.ansible_strategy('linear')
def test_complete_single_linear(ansible_play):
    trace_hosts: Dict[int, HostEvent]
    trace_events: Dict[int, List[List[Any]]]
    trace_json: JSONTYPE = get_last_trace()
    trace_hosts, trace_events = parse_and_validate_trace(trace_json)

import os
import json
import glob
import re
from collections import deque
from typing import Union, Dict, List, Any, TextIO, Deque, Tuple
from event import HostEvent, DurationEvent

JSONTYPE = Union[None, int, str, bool, List[Any], Dict[str, Any]]


def get_last_trace() -> JSONTYPE:
    list_of_files: List[str] = glob.glob('trace/*')
    latest_file: str = max(list_of_files, key=os.path.getctime)

    file: TextIO = open(latest_file, encoding="utf-8")
    trace_json: JSONTYPE = json.load(file)
    file.close()
    return trace_json


def parse_and_validate_trace(trace: JSONTYPE) -> Tuple[Dict[int, HostEvent],
                                                       Dict[int, Any]]:
    hosts: Dict[int, HostEvent] = {}
    duration_events: Dict[int, Any] = {}
    duration_stacks: Dict[int, Deque] = {}

    # Parse events in trace
    for event in trace:
        if 'ph' in event and event['ph'] == 'M':
            hosts, duration_events, duration_stacks = add_hosts(
                hosts, duration_events, duration_stacks, event)
        elif 'ph' in event and re.search("^(B|E)$", event['ph']):
            duration_events, duration_stacks = add_duration_event(
                hosts, duration_events, duration_stacks, event)
        else:
            raise ValueError('Event cannot be handled')

    return (hosts, duration_events)


def add_hosts(
        hosts: Dict[int, HostEvent],
        duration_events: Dict[int, Any],
        duration_stacks: Dict[int, Deque],
        event_hash: Any) -> Tuple[Dict[int, HostEvent],
                                  Dict[int, Any], Dict[int, Deque]]:

    event = HostEvent(event_hash)

    hosts[event.pid] = event
    duration_events[event.pid] = {}
    duration_stacks[event.pid] = deque()

    return (hosts, duration_events, duration_stacks)


def add_duration_event(
        hosts: Dict[int, HostEvent],
        events: Dict[int, Any],
        curr_stacks: Dict[int, Deque],
        event_hash: Any) -> Tuple[Dict[int, Any], Dict[int, Deque]]:

    event = DurationEvent(event_hash)

    if event.pid not in hosts:
        raise ValueError(
            f'Duration event {event.id} host with pid {event.pid}'
            'does not match any registered host')

    if event.ph == 'B':

        # Check if event already exists
        if event.id in events[event.pid]:
            raise ValueError(f'Event {event.id} already registered')

        events[event.pid][event.id] = {'B': event, 'children_ids': []}

        # If there is event in stack, must declare this event as child of last
        # event in stack
        if curr_stacks[event.pid]:
            parent_id: int = curr_stacks[event.pid][-1]
            if parent_id not in events[event.pid]:
                raise ValueError(
                    f'Event id {parent_id} in stack, '
                    'is not present in host events')

            # Check if child timestamp is inferior or equal to parent
            if events[event.pid][parent_id]['B'].ts > event.ts:
                raise ValueError(f'Event id {event.id}'
                                 f'begin timestamp {event.ts}'
                                 'is inferior to its parent id'
                                 f'{events[event.pid][parent_id]["B"].id}'
                                 'with timestamp'
                                 f'{events[event.pid][parent_id]["B"].ts}')

            events[event.pid][parent_id]['children_ids'].append(event.id)
            events[event.pid][event.id]['parent_id'] = parent_id

        curr_stacks[event.pid].append(event.id)
        return (events, curr_stacks)

    if event.ph == 'E':

        # Check if there is B event
        if (event.id not in events[event.pid]
                or 'B' not in events[event.pid][event.id]):
            raise ValueError(f'Event {event.id} is not registered')

        # Check if timestamp is superior or equal to B event
        if events[event.pid][event.id]['B'].ts > event.ts:
            raise ValueError(f'Event id {event.id} timestamp {event.ts}'
                             'is lower than its begin event with timestamp'
                             f'{events[event.pid][event.id]["B"].ts}')

        # Check we don't have children event not yet ended
        if(not curr_stacks[event.pid]
                or curr_stacks[event.pid][-1] != event.id):
            raise ValueError(
                f'Cannot end event id {event.id}'
                'if I have child that are not yet ended'
                f'(id {curr_stacks[event.pid][-1]} ongoing)')

        # Check E event has the same name than the B events
        if events[event.pid][event.id]['B'].name != event.name:
            raise ValueError(f'Event id {event.id} with name {event.name}'
                             ' does not have the same name as event B'
                             f'{events[event.pid][event.id]["B"].name}')

        events[event.pid][event.id]['E'] = event
        curr_stacks[event.pid].pop()

    return (events, curr_stacks)

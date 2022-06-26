import os
import json
import glob
import re
from typing import Union, Dict, List, Any, TextIO, Tuple
from event import HostEvent, DurationEvent

JSONTYPE = Union[None, int, str, bool, List[Any], Dict[str, Any]]


def get_last_trace() -> JSONTYPE:
    list_of_files: List[str] = glob.glob('trace/*')
    latest_file: str = max(list_of_files, key=os.path.getctime)

    file: TextIO = open(latest_file, encoding="utf-8")
    trace_json: JSONTYPE = json.load(file)
    file.close()
    return trace_json


def parse_and_validate_trace(
    trace: JSONTYPE) -> Tuple[Dict[int, HostEvent],
                              Dict[int, List[List[Any]]]]:
    hosts: Dict[int, HostEvent] = {}
    duration_events: Dict[int, List[List[Any]]] = {}

    # Parse events in trace
    for event in trace:
        if 'ph' in event and event['ph'] == 'M':
            hosts, duration_events = add_hosts(
                hosts, duration_events, event)
        elif 'ph' in event and re.search("^(B|E)$", event['ph']):
            duration_events = add_duration_event(
                hosts, duration_events, event)
        else:
            raise ValueError('Event cannot be handled')

    return (hosts, duration_events)


def add_hosts(
        hosts: Dict[int, HostEvent],
        duration_events: Dict[int, List[List[Any]]],
        event_hash: Any) -> Tuple[Dict[int, HostEvent],
                                  Dict[int, List[List[Any]]]]:

    event = HostEvent(event_hash)

    hosts[event.pid] = event
    duration_events[event.pid] = []

    return (hosts, duration_events)


def add_duration_event(
        hosts: Dict[int, HostEvent],
        event_matrix: Dict[int, List[List[Any]]],
        event_hash: Any) -> Dict[int, List[List[Any]]]:

    event = DurationEvent(event_hash)

    if event.pid not in hosts:
        raise ValueError(
            f'Duration event {event.id} host with pid {event.pid}'
            'does not match any registered host')

    if event.ph == 'B':
        # If first event of the last stack is finished, add new stack
        if(len(event_matrix[event.pid]) == 0 or
           'E' in event_matrix[event.pid][-1][0]):
            event_matrix[event.pid].append([{'B': event}])
        # Else check the last parent of the last stack
        # and ensure child timestamp is inferior
        else:
            last_parent = None
            for elem in event_matrix[event.pid][-1][::-1]:
                if 'E' not in elem:
                    last_parent = elem
                    break
            if last_parent['B'].ts > event.ts:
                raise ValueError(f'Event id {event.id}'
                                 f'begin timestamp {event.ts}'
                                 'is inferior to its parent id'
                                 f'{last_parent["B"].id}'
                                 'with timestamp'
                                 f'{last_parent["B"].ts}')
            event_matrix[event.pid][-1].append({'B': event})

    else:
        # Get element to end
        event_to_end = None
        for elem in event_matrix[event.pid][-1][::-1]:
            if elem['B'].id == event.id:
                event_to_end = elem
                break
        if event_to_end is None:
            raise ValueError(f'Event {event.id} is not registered')

        # Check if timestamp is superior or equal to B event
        if event_to_end["B"].ts > event.ts:
            raise ValueError(f'Event id {event.id} timestamp {event.ts}'
                             'is lower than its begin event with timestamp'
                             f'{event_to_end["B"].ts}')

        # Check E event has the same name than the B events
        if event_to_end["B"].name != event.name:
            raise ValueError(f'Event id {event.id} with name {event.name}'
                             ' does not have the same name as event B'
                             f'{event_to_end["B"].name}')

        event_to_end['E'] = event

    return event_matrix

import os
import json
import glob
import re
from collections import deque
from typing import Union, Dict, List, Any, TextIO, NewType, Deque, Tuple
from event import HostEvent, DurationEvent

JSONTYPE = Union[None, int, str, bool, List[Any], Dict[str, Any]]

def get_last_trace() -> JSONTYPE:
    list_of_files: List[str] = glob.glob('trace/*')
    latest_file: str = max(list_of_files, key=os.path.getctime)
    
    f: TextIO = open(latest_file)
    trace_json: JSONTYPE = json.load(f)
    f.close()
    return trace_json

def parse_trace(trace: JSONTYPE) -> Tuple[Dict[int, HostEvent], Dict[int, Any]]:
    hosts: Dict[int, HostEvent] = {}
    duration_events: Dict[int, Any]  = {}
    duration_stacks: Dict[int, Deque] = {}

    # Parse events in trace
    for event in trace:
        if 'ph' in event and event['ph'] == 'M':
            hosts, duration_events, duration_stacks = add_hosts(hosts, duration_events, duration_stacks, event)
        elif 'ph' in event and re.search("^(B|E)$", event['ph']):
            duration_events, duration_stacks = add_duration_event(hosts, duration_events, duration_stacks, event)  
        else:
           raise ValueError('Event cannot be handled') 

    return (hosts, duration_events)

def add_hosts(hosts: Dict[int, HostEvent], duration_events: Dict[int, Any], duration_stacks: Dict[int, Deque], event_hash: Any) -> Tuple[Dict[int, HostEvent], Dict[int, Any], Dict[int, Deque]]:

    event = HostEvent(event_hash)

    hosts[event.pid] = event
    duration_events[event.pid] = {}
    duration_stacks[event.pid] = deque()

    return (hosts, duration_events, duration_stacks)

def add_duration_event(hosts: Dict[int, HostEvent], events: Dict[int, Any], curr_stacks: Dict[int, Deque], event_hash: Any) -> Tuple[Dict[int, Any], Dict[int, Deque]]:
   
    event = DurationEvent(event_hash)

    if not event.pid in hosts:
        raise ValueError('Duration event {} host with pid {} does not match any registered host'.format(event.id, event.pid))

    if event.ph == 'B':

        # Check if event already exists
        if event.id in events[event.pid]:
            raise ValueError('Event {} already registered'.format(event.id))

        events[event.pid][event.id] = {'B': event, 'children_ids': []}

        # If there is event in stack, must declare this event as child of last event in stack
        if curr_stacks[event.pid]:
            parent_id: int = curr_stacks[event.pid][-1]
            if not parent_id in events[event.pid]:
                raise ValueError('Event id {} in stack, is not present in host events'.format(parent_id))

            # Check if child timestamp is inferior or equal to parent
            if events[event.pid][parent_id]['B'].ts > event.ts:
                raise ValueError('Event id {} begin timestamp {} is inferior to its parent id {} with timestamp {}'.format(event.id, event.ts, events[event.pid][parent_id]['B'].id, events[event.pid][parent_id]['B'].ts))

            events[event.pid][parent_id]['children_ids'].append(event.id)
            events[event.pid][event.id]['parent_id'] = parent_id

        curr_stacks[event.pid].append(event.id)
        return (events, curr_stacks)
    
    if event.ph == 'E':

        # Check if there is B event
        if not event.id in events[event.pid] or not 'B' in events[event.pid][event.id]:
            raise ValueError('Event {} is not registered'.format(event.id))

        # Check if timestamp is superior or equal to B event
        if events[event.pid][event.id]['B'].ts > event.ts:
            raise ValueError('Event id {} timestamp {} is lower than its begin event with timestamp {}'.format(event.id, event.ts, events[event.pid][event.id]['B'].ts))

        # Check we don't have children event not yet ended
        if not curr_stacks[event.pid] or curr_stacks[event.pid][-1] != event.id:
            raise ValueError('Cannot end event id {} if I have child that are not yet ended (id {} ongoing)'.format(event.id, curr_stacks[event.pid][-1]))

        events[event.pid][event.id]['E'] = event
        curr_stacks[event.pid].pop()

    return (events, curr_stacks)


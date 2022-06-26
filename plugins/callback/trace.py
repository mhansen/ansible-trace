# Copyright 2021 Google LLC
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# version 3 as published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from typing import Any, Deque, Dict, TextIO
from datetime import datetime
from dataclasses import dataclass, field
from collections import deque
import time
import os
import json
import atexit
from ansible.plugins.callback import CallbackBase

DOCUMENTATION = '''
    name: trace
    type: aggregate
    short_description: Write playbook output to Chrome\'s Trace Event Format file
    description:
      - This callback writes playbook output to Chrome Trace Event Format file.
    author: Mark Hansen (@mhansen)
    options:
      trace_output_dir:
        name: output dir
        default: ./trace
        description: Directory to write files to.
        env:
          - name: TRACE_OUTPUT_DIR
      hide_task_arguments:
        name: Hide the arguments for a task
        default: False
        description: Hide the arguments for a task
        env:
          - name: HIDE_TASK_ARGUMENTS
    requirements:
      - enable in configuration
'''


class CallbackModule(CallbackBase):
    """
    This callback traces execution time of tasks to Trace Event Format.

    This plugin makes use of the following environment variables:
        TRACE_OUTPUT_DIR (optional): Directory to write JSON files to.
                                     Default: ./trace
        TRACE_HIDE_TASK_ARGUMENTS (optional): Hide the arguments for a task
                                     Default: False
    """

    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'aggregate'
    CALLBACK_NAME = 'trace'
    CALLBACK_NEEDS_ENABLED = True

    def __init__(self):
        super(CallbackModule, self).__init__()

        self._output_dir: str = os.getenv(
            'TRACE_OUTPUT_DIR', os.path.join(os.path.expanduser('.'), 'trace'))
        self._hide_task_arguments: str = os.getenv(
            'TRACE_HIDE_TASK_ARGUMENTS', 'False').lower()
        self._hosts: Dict[Host] = {}
        self._next_pid: int = 1
        self._first: bool = True
        self._start_date: str = datetime.now().isoformat()
        self._output_file: str = f'trace-{self._start_date}.json'
        self._current_play: Any = None
        self._tasks: Dict[str] = {}

        if not os.path.exists(self._output_dir):
            os.makedirs(self._output_dir)
        output_file = os.path.join(self._output_dir, self._output_file)
        self._f: TextIO = open(output_file, 'w')
        self._f.write("[\n")

        atexit.register(self._end)

    def _get_time(self):
        return time.time_ns() / 1000 if "time_ns" in time.__dict__ else time.time() * 100000

    def _write_event(self, e: Dict):
        if not self._first:
            self._f.write(",\n")
        self._first = False
        # sort for reproducibility
        json.dump(e, self._f, sort_keys=True, indent=2)
        self._f.flush()

    def v2_runner_on_start(self, host, task):
        uuid = task._uuid
        name = self._tasks[uuid]

        args = None
        if not task.no_log and self._hide_task_arguments == 'false':
            args = task.args

        host_uuid = host._uuid
        if host_uuid not in self._hosts:
            self._register_host(host)

        # If it's the first task of the host for the play, start duration event for the current play
        if not self._hosts[host_uuid].has_task_in_play:
            self._start_play_span(host)

        # Handle role spans
        self._role_span(host, task)

        # Start task duration event
        # See "Duration Events" in:
        # https://docs.google.com/document/d/1CvAClvFfyA5R-PhYUmn5OOQtYMH4h6I0nSsKchNAySU/preview#heading=h.nso4gcezn7n1
        self._write_event({
            "name": name,
            "cat": "runner",
            "ph": "B",  # Begin
            "ts": self._get_time(),
            "pid": self._hosts[host_uuid].pid,
            "id": abs(hash(uuid)),
            "args": {
                "args": args,
                "task": name,
                "path": task.get_path(),
                "host": host.name,
            },
        })
        self._hosts[host_uuid].last_runner_begin_ts = self._get_time()

    def v2_playbook_on_play_start(self, play):
        self._end_all_role_span()
        self._end_play_span()
        self._current_play = play

    def v2_playbook_on_task_start(self, task, is_conditional):
        self._tasks[task._uuid] = task.name.strip()

    def _register_host(self, host):
        pid = self._next_pid
        self._hosts[host._uuid] = Host(pid=pid, name=host.name)
        self._next_pid += 1

        # See Metadata Events in:
        # https://docs.google.com/document/d/1CvAClvFfyA5R-PhYUmn5OOQtYMH4h6I0nSsKchNAySU/preview#bookmark=id.iycbnb4z7i9g

        self._write_event({
            "name": "process_name",
            "pid": pid,
            "cat": "process",
            "ph": "M",
            "args": {
                "name": host.name,
            },
        })

    def _start_play_span(self, host):
        self._write_event({
            "name": self._current_play.get_name().strip(),
            "cat": "play",
            "ph": "B",  # Begin
            "ts": self._get_time(),
            "pid": self._hosts[host._uuid].pid,
            "id": abs(hash(self._current_play._uuid)),
            "args": {
                "host": host.name,
            },
        })
        self._hosts[host._uuid].has_task_in_play = True

    def _end_play_span(self):
        # Spawn ending play event for each play that are done and then reset flag
        for host in self._hosts.values():
            if host.has_task_in_play:
                # Write end event
                self._write_event({
                    "name": self._current_play.get_name().strip(),
                    "cat": "play",
                    "id": abs(hash(self._current_play._uuid)),
                    "ph": "E",  # End
                    "ts": host.last_runner_end_ts,
                    "pid": host.pid,
                })

                host.has_task_in_play = False

    def _role_span(self, host, task):

        # End all current role if done
        while(self._hosts[host._uuid].role_stack
              and host.name in self._hosts[host._uuid].role_stack[-1]._completed):

            # Do not end current role event marked as completed if we are currently in it
            # Duplicates roles are marked as completed after first occurence
            if(task._role is not None and
               task._role.get_name() == self._hosts[host._uuid].role_stack[-1].get_name()):
                break

            self._end_role_span(
                self._hosts[host._uuid], self._hosts[host._uuid].role_stack[-1])

        # Create B role event if required
        if task._role is not None:

            # Still in current role, nothing to do
            if(self._hosts[host._uuid].role_stack and
               self._hosts[host._uuid].role_stack[-1].get_name() ==
               task._role.get_name()):
                return

            # Declare Parents not yet in role stack (happen when import_roles at start of role)
            if task._role._parents:
                for parent in task._role._parents[::-1]:
                    if parent.from_include:
                        continue
                    if(not parent.get_name() in
                       list(map(lambda x: x.get_name(), self._hosts[host._uuid].role_stack))):
                        self._start_role_span(host, parent)

            self._start_role_span(host, task._role)

    def _end_all_role_span(self):
        # Handle for roles that finish at the end of play
        for host in self._hosts.values():
            while(host.role_stack):
                self._end_role_span(host, host.role_stack[-1])

    def _start_role_span(self, host, role):
        name: str = role.get_name().strip()

        self._write_event({
            "name": name,
            "cat": "role",
            "ph": "B",  # Begin
            "ts": self._get_time(),
            "pid": self._hosts[host._uuid].pid,
            "id": abs(hash(role._uuid)),
            "args": {
                "role": name,
                "path": role._role_path,
                "host": host.name,
            },
        })
        self._hosts[host._uuid].role_stack.append(role)

    def _end_role_span(self, host, role):
        name: str = role.get_name().strip()
        self._write_event({
            "name": name,
            "cat": "role",
            "id": abs(hash(role._uuid)),
            "ph": "E",  # End
            "ts": host.last_runner_end_ts,
            "pid": host.pid
        })
        host.role_stack.pop()

    def _end_task_span(self, result, status: str):
        task = result._task
        uuid = task._uuid
        now: float = self._get_time()

        self._write_event({
            "name": task.name.strip(),
            "cat": "runner",
            "id": abs(hash(uuid)),
            "ph": "E",  # End
            "ts": now,
            "pid": self._hosts[result._host._uuid].pid,
            "args": {
                "status": status,
            },
        })
        self._hosts[result._host._uuid].last_runner_end_ts = now

    def v2_runner_on_ok(self, result):
        self._end_task_span(result, status="ok")

    def v2_runner_on_unreachable(self, result):
        self._end_task_span(result, 'unreachable')

    def v2_runner_on_failed(self, result, ignore_errors=False):
        self._end_task_span(result, status='failed')

    def v2_runner_on_skipped(self, result):
        self._end_task_span(result, status='skipped')

    def _item_span(self, result, status: str):
        item: Any = result._result['_ansible_item_label']
        name = str(item)

        # Try to have a nice name when item is a dict
        if isinstance(item, dict) and 'name' in item:
            name = item['name']

        self._write_event({
            "name": name,
            "cat": "item",
            "id": abs(hash(self._hosts[result._host._uuid].item_id)),
            "ph": "B",  # Begin
            "ts": self._hosts[result._host._uuid].last_runner_begin_ts,
            "pid": self._hosts[result._host._uuid].pid,
            "args": {}
        })

        now: float = self._get_time()
        self._write_event({
            "name": name,
            "cat": "item",
            "id": abs(hash(self._hosts[result._host._uuid].item_id)),
            "ph": "E",  # End
            "ts": self._get_time(),
            "pid": self._hosts[result._host._uuid].pid,
            "args": {
                "status": status,
            },
        })
        self._hosts[result._host._uuid].item_id += 1
        self._hosts[result._host._uuid].last_runner_end_ts = now
        # Has to be different from ending time to avoid errors
        self._hosts[result._host._uuid].last_runner_begin_ts = self._get_time()

    def v2_runner_item_on_ok(self, result):
        self._item_span(result, status="ok")

    def v2_runner_item_on_failed(self, result):
        self._item_span(result, status="failed")

    def v2_runner_item_on_skipped(self, result):
        self._item_span(result, status="skipped")

    def _end(self):
        self._end_all_role_span()
        self._end_play_span()
        self._f.write("\n]")
        self._f.close()


@ dataclass
class Host:
    name: str
    pid: int
    last_runner_end_ts: float = None
    last_runner_begin_ts: float = None
    has_task_in_play: bool = False
    role_stack: Deque = field(default_factory=deque)
    item_id: int = 0

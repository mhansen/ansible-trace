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


DOCUMENTATION = '''
    name: trace
    type: aggregate
    short_description: write playbook output to Chrome's Trace Event Format file
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

import json
import os
import time
from dataclasses import dataclass
from typing import Dict, TextIO

from ansible.plugins.callback import CallbackBase


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

        self._output_dir: str = os.getenv('TRACE_OUTPUT_DIR', os.path.join(os.path.expanduser('.'), 'trace'))
        self._hide_task_arguments: str = os.getenv('TRACE_HIDE_TASK_ARGUMENTS', 'False').lower()
        self._hosts: Dict[Host] = {}
        self._next_pid: int = 1
        self._first: bool = True

        if not os.path.exists(self._output_dir):
            os.makedirs(self._output_dir)
        output_file = os.path.join(self._output_dir, 'trace.json')
        self._f: TextIO = open(output_file, 'w')

    def _write_event(self, e: Dict):
        if self._first:
            self._f.write("[\n")
        else:
            self._f.write(",\n")
        self._first = False
        json.dump(e, self._f, sort_keys=True, indent=2) # sort for reproducibility
        self._f.flush()

    def v2_runner_on_start(self, host, task):
        uuid = task._uuid
        name = task.get_name().strip()

        args = None
        if not task.no_log and self._hide_task_arguments == 'false':
            args = task.args

        host_uuid = host._uuid
        if host_uuid not in self._hosts:
            pid = self._next_pid
            self._hosts[host_uuid] = Host(pid=pid, name=host.name)
            self._next_pid += 1
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

        # See "Duration Events" in:
        # https://docs.google.com/document/d/1CvAClvFfyA5R-PhYUmn5OOQtYMH4h6I0nSsKchNAySU/preview#heading=h.nso4gcezn7n1
        self._write_event({
            "name": name,
            "cat": "runner",
            "ph": "B",  # Begin
            "ts": time.time_ns() / 1000,
            "pid": self._hosts[host_uuid].pid,
            "id": abs(hash(uuid)),
            "args": {
                "args": args,
                "task": name,
                "path": task.get_path(),
                "host": host.name,
            },
        })


    def _end_span(self, result, status: str):
        task = result._task
        uuid = task._uuid
        # See "Duration Events" in:
        # https://docs.google.com/document/d/1CvAClvFfyA5R-PhYUmn5OOQtYMH4h6I0nSsKchNAySU/preview#heading=h.nso4gcezn7n1
        self._write_event({
            "name": task.get_name().strip(),
            "cat": "runner",
            "id": abs(hash(uuid)),
            "ph": "E",  # End
            "ts": time.time_ns() / 1000,
            "pid": self._hosts[result._host._uuid].pid,
            "args": {
                "status": status,
            },
        })

    def v2_runner_on_ok(self, result):
        self._end_span(result, status="ok")

    def v2_runner_on_unreachable(self, result):
        self._end_span(result, 'unreachable')

    def v2_runner_on_failed(self, result, ignore_errors=False):
        self._end_span(result, status='failed')

    def v2_runner_on_skipped(self, result):
        self._end_span(result, status='skipped')

    def v2_playbook_on_stats(self, stats):
        self._f.write("\n]")
        self._f.close()

@dataclass
class Host:
    name: str
    pid: int

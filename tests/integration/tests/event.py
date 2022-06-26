import re


class Event:

    pid: int
    name: str
    ph: str

    def __init__(self, dict):
        if 'pid' not in dict:
            raise ValueError('Event must be linked to pid')
        self.pid = dict['pid']
        self.ph = dict['ph']


class DurationEvent(Event):

    id: int
    ts: float

    def __init__(self, dict):
        if 'id' not in dict:
            raise ValueError('Duration event needs to have id')
        self.id = dict['id']
        if 'ts' not in dict:
            raise ValueError(f'Duration event {self.id} needs to have a timestamp')
        if 'name' not in dict:
            raise ValueError(f'Duration event {self.id} needs to have a name')
        if 'ph' not in dict or not re.search("^(B|E)$", dict['ph']):
            raise ValueError(
                f'Duration event {self.id} needs to have a ph either set to B or E')
        self.ts = dict['ts']
        self.name = dict['name']

        super().__init__(dict)


class HostEvent(Event):

    def __init__(self, dict):
        if 'ph' not in dict or dict['ph'] != 'M':
            raise ValueError('Host event needs to have a ph set to M')
        if 'args' not in dict or 'name' not in dict['args']:
            raise ValueError('Host events needs to have name')

        self.name = dict['args']['name']

        super().__init__(dict)

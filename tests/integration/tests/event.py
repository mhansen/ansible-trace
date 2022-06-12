import re

class Event:

    pid: int
    name: str
    ph: str

    def __init__(self, dict):
        if not 'pid' in dict:
            raise ValueError('Event must be linked to pid')
        self.pid = dict['pid']
        self.ph = dict['ph']

class DurationEvent(Event):

    id: int
    ts: float

    def __init__(self, dict):
        if not 'id' in dict:
            raise ValueError('Duration event needs to have id')
        self.id = dict['id']
        if not 'ts' in dict:
            raise ValueError('Duration event {} needs to have a timestamp'.format(self.id))
        if not 'name' in dict:
            raise ValueError('Duration event {} needs to have a name'.format(self.id))
        if not 'ph' in dict or not re.search("^(B|E)$", dict['ph']):
            raise ValueError('Duration event {} needs to have a ph either set to B or E'.format(self.id))
        self.ts = dict['ts']
        self.name = dict['name']

        super().__init__(dict)

class HostEvent(Event):

    def __init__(self, dict):
        if not 'ph' in dict or dict['ph'] != 'M':
            raise ValueError('Host event needs to have a ph set to M')
        if not 'args' in dict or not 'name' in dict['args']:
            raise ValueError('Host events needs to have name')

        self.name = dict['args']['name']

        super().__init__(dict)


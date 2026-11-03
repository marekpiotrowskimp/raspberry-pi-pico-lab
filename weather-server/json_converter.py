import json
from collections import namedtuple

class JsonConverter:
    def json_object_hook(self, d):
        return namedtuple('X', d.keys())(*d.values())

    def json2obj(self, data):
        return json.loads(data, object_hook=self.json_object_hook)
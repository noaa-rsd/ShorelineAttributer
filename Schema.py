import json
import os
from pathlib import Path
import arcpy


class Schema:

    def __init__(self, path):
        self.path = path
        self.set_attributes()
        self.atypes = {
            'tile': [
                'DATA_SOURC',
                'FEATURE',
                'EXTRACT_TE',
                'RESOLUTION',
                'CLASS',
                'ATTRIBUTE',
                'INFORM',
                'HOR_ACC',
                'SRC_DATE',
                'SOURCE_ID',
                'EXT_METH'
                ],
            'line': []
            }

    def __str__(self):
        return json.dumps(self.__dict__, indent=1)

    def set_attributes(self):
        with open(self.path, 'r') as j:
            gc_schema = json.load(j)
            self.__dict__ = gc_schema['FINAL']['LINES']


if __name__ == '__main__':
    cwd = os.path.dirname(os.path.realpath(__file__))
    os.chdir(cwd)

    schema_path = Path(r'.\Appendix5Attributes.json')
    schema = Schema(schema_path)

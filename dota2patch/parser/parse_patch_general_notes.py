import json
from functools import reduce


class ParsePatchGeneralNotes:
    def parse(self, general_note, patch_metadata):
        return {
            'patch_metadata': patch_metadata,
            'type': 'generic',
            'changes': " ".join(note.get('note') + '.' for note in general_note.get('generic')),
            'title': general_note.get('title', 'Generic Changes')
        }

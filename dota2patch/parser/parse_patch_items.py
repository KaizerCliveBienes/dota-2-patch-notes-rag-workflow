class ParsePatchItems:
    def __init__(self, item_raw_data):
        self.items_mapping = self.construct_item_mapping(item_raw_data)

    def construct_item_mapping(self, raw_data):
        item_abilities = raw_data['result']['data']['itemabilities']
        item_ability_mapping = {}
        for item_ability in item_abilities:
            item_ability_mapping[item_ability['id']] = item_ability['name_loc']
        return item_ability_mapping

    def parse(self, item_note, patch_metadata, item_subtype):
        if item_note['ability_id'] == -1:
            return None

        changes = [
            f"{note['note']}{
                f'({note['info']})' if 'info' in note else ''}."
            for note in item_note.get('ability_notes', [])
        ]

        return {
            'patch_metadata': patch_metadata,
            'type': 'items',
            'subtype': item_subtype,
            'changes': ' '.join(changes),
            'title': self.items_mapping.get(item_note['ability_id'], ''),
        }

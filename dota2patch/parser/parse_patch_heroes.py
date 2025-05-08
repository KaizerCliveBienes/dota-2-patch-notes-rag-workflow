import json
from functools import reduce

class ParsePatchHeroes:
    def __init__(self, hero_raw_data, ability_raw_data):
        self.heroes_mapping = self.construct_hero_mapping(hero_raw_data)
        self.abilities_mapping = self.construct_ability_mapping(ability_raw_data)

    def construct_hero_mapping(self, raw_data):
        item_abilities = raw_data['result']['data']['heroes']
        item_ability_mapping = {}
        for item_ability in item_abilities:
            item_ability_mapping[item_ability['id']] = item_ability['name_loc']
        return item_ability_mapping

    def construct_ability_mapping(self, raw_data):
        abilities = raw_data['result']['data']['itemabilities']
        ability_mapping = {}
        for ability in abilities:
            ability_mapping[ability['id']] = ability['name_loc'] 

        return ability_mapping

    def parse(self, hero_note, patch_metadata):
        if hero_note['hero_id'] == -1:
            return None

        hero_updates = []
        if 'abilities' in hero_note:
            for ability in hero_note['abilities']:
                hero_updates.append({
                    'patch_metadata': patch_metadata,
                    'type': 'heroes',
                    'subtype': 'abilities',
                    'skill_name': self.abilities_mapping[ability['ability_id']],
                    'changes': ' '.join(note['note'] + ('(' + note['info'] + ')' if 'info' in note else '') + '.' for note in ability['ability_notes']),
                    'title': self.heroes_mapping[hero_note['hero_id']] if hero_note['hero_id'] in self.heroes_mapping else '',
                })
            
        if 'subsections' in hero_note:
            for subsection in hero_note['subsections']:
                if 'facet' in subsection:
                    abilities = subsection['abilities'] if 'abilities' in subsection else []
                    changes = ' '.join(note['note'] + ('(' + note['info'] + ')' if 'info' in note else '') + '.' for note in (subsection['general_notes'] if 'general_notes' in subsection else []))

                    hero_updates.append({
                        'patch_metadata': patch_metadata,
                        'type': 'heroes',
                        'subtype': 'facets',
                        'skill_name': subsection['title'],
                        'changes': changes if changes else ' '.join(self.abilities_mapping[ability['ability_id']] + ': ' + note['note'] + ('(' + note['info'] + ')' if 'info' in note else '') + '.' for ability in abilities for note in ability['ability_notes']),
                        'title': self.heroes_mapping[hero_note['hero_id']] if hero_note['hero_id'] in self.heroes_mapping else '',
                    })

        return hero_updates

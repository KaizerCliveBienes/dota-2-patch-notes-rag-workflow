class ParsePatchHeroes:
    def __init__(self, hero_raw_data, ability_raw_data):
        self.heroes_mapping = self.construct_hero_mapping(hero_raw_data)
        self.abilities_mapping = self.construct_ability_mapping(
            ability_raw_data)

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
                changes = [
                    f"{note['note']}{
                        f'({note['info']})' if 'info' in note else ''}."
                    for note in ability['ability_notes']
                ]

                title = self.heroes_mapping.get(hero_note['hero_id'], '')

                skill_name = self.abilities_mapping.get(
                    ability['ability_id'], '')

                hero_updates.append({
                    'patch_metadata': patch_metadata,
                    'type': 'heroes',
                    'subtype': 'abilities',
                    'skill_name': skill_name,
                    'changes': ' '.join(changes),
                    'title': title,
                })

        if 'subsections' in hero_note:
            for subsection in hero_note['subsections']:
                if 'facet' in subsection:
                    abilities = subsection.get('abilities', [])
                    changes = [
                        f"{note['note']}{
                            f'({note['info']})' if 'info' in note else ''}."
                        for note in subsection.get('general_notes', [])
                    ]

                    ability_changes = [
                        f"{self.abilities_mapping.get(
                            ability['ability_id'], '')}:{note['note']}{
                            f'({note['info']})' if 'info' in note else ''}"
                        for ability in abilities for note in ability.get(
                            'ability_notes', [])
                    ]

                    title = self.heroes_mapping.get(hero_note['hero_id'], '')

                    hero_updates.append({
                        'patch_metadata': patch_metadata,
                        'type': 'heroes',
                        'subtype': 'facets',
                        'skill_name': subsection['title'],
                        'changes': ' '.join(
                            changes if changes else ability_changes),
                        'title': title,
                    })

        return hero_updates

import requests
import json
from ..parser.parse_patch_general_notes import ParsePatchGeneralNotes
from ..parser.parse_patch_items import ParsePatchItems
from ..parser.parse_patch_heroes import ParsePatchHeroes
from ..database.process_data import ProcessData


class PatchFetcher():
    def fetch_and_parse_json(self, url):
        """
        Fetches data from a URL and attempts to parse it as JSON.

        Args:
            url (str): The URL to fetch data from.

        Returns:
            dict or list or None: The parsed JSON data as a Python dictionary or list,
                                or None if an error occurred.
        """
        try:
            response = requests.get(url)
            response.raise_for_status()
            json_data = response.json()
            return json_data
        except requests.exceptions.RequestException as e:
            print(f"Error fetching URL: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {e}")
            print(f"Response text: {response.text}")
            return None

    def construct_all_patch_documents(self, patch_version):
        parse_patch_general_notes = ParsePatchGeneralNotes()

        # patch metadata
        patch_data = self.fetch_and_parse_json(
            f'https://www.dota2.com/datafeed/patchnotes?version={patch_version}&language=english')
        patch_metadata = {
            'patch_number': patch_data['patch_number'],
            'patch_name': patch_data['patch_name'],
        }
        general_notes = list(
            map(
                lambda note: parse_patch_general_notes.parse(
                    note, patch_metadata),
                patch_data['general_notes'],
            )
        )

        # patch item notes
        item_data = self.fetch_and_parse_json(
            "https://www.dota2.com/datafeed/itemlist?language=english")
        parse_patch_items = ParsePatchItems(item_data)
        item_notes = list(
            filter(
                lambda x: x is not None,
                map(
                    lambda item: parse_patch_items.parse(
                        item, patch_metadata, 'hero_items'),
                    patch_data['items'],
                )
            )
        )

        neutral_item_notes = list(
            filter(
                lambda x: x is not None,
                map(
                    lambda item: parse_patch_items.parse(
                        item, patch_metadata, 'neutral_items'),
                    patch_data['neutral_items'],
                )
            )
        )

        # hero item notes
        hero_data = self.fetch_and_parse_json(
            "https://www.dota2.com/datafeed/herolist?language=english")
        ability_data = self.fetch_and_parse_json(
            "https://www.dota2.com/datafeed/abilitylist?language=english")
        parse_patch_heroes = ParsePatchHeroes(hero_data, ability_data)
        hero_notes = list(
            filter(
                lambda x: x is not None,
                map(
                    lambda item: parse_patch_heroes.parse(
                        item, patch_metadata),
                    patch_data['heroes'],
                )
            )
        )

        process_data = ProcessData()
        all_patch_documents = []
        for patch_notes in [general_notes, item_notes, neutral_item_notes]:
            all_patch_documents.append(
                process_data.load_and_process_data(patch_notes))

        all_patch_documents.append(
            process_data.load_and_process_hero_data(hero_notes))

        return all_patch_documents

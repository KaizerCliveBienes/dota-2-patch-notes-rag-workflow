import requests
import json


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

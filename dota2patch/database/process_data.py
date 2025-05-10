from langchain.docstore.document import Document


class ProcessData:
    def load_and_process_data(self, json_data):
        documents = []

        for entry in json_data.get('items', []):
            page_content = self.construct_page_content(entry)
            metadata = self.process_metadata(entry, page_content)
            if metadata is None:
                continue

            documents.append(
                Document(
                    page_content=page_content,
                    metadata=metadata))

        print(f"Loaded changes for {json_data.get('type', '')}")
        return documents

    def load_and_process_hero_data(self, json_data):
        documents = []

        for hero_entries in json_data.get('items', []):
            for entry in hero_entries:
                page_content = self.construct_page_content(entry)
                metadata = self.process_metadata(entry, page_content)
                if metadata is None:
                    continue

                documents.append(
                    Document(
                        page_content=page_content,
                        metadata=metadata))

        print(f"Loaded changes for {json_data.get('type', '')}")
        return documents

    def construct_page_content(self, entry):
        patch = entry.get("patch_metadata", {}).get("patch_name", "")
        type_string = entry.get("type", "")
        subtype = f"({entry.get('subtype')})" if 'subtype' in entry else ""
        title = entry.get("title", "")
        skill = f" - {entry.get('skill_name', '')}"
        changes = entry.get("changes", "")
        return f'Patch "{patch}" for {type_string}{subtype}: {
            title}{skill} - {changes}'

    def process_metadata(self, entry, page_content):
        if not page_content:
            print(
                f"Skipping entry due to missing 'changes' field: {
                    entry.get('title')}")
            return None

        metadata = {
            "patch_number": entry.get("patch_metadata", {})
            .get("patch_number", "N/A"),
            "patch_name": entry.get("patch_metadata", {})
            .get("patch_name", "N/A"),
            "type": entry.get("type", "N/A"),
            "subtype": entry.get("subtype", "N/A"),
            "title": entry.get("title", "N/A"),
            # Storing the original text is good practice
            "original_change_text": page_content
        }
        if "skill_name" in entry:
            metadata["skill_name"] = entry["skill_name"]

        return metadata

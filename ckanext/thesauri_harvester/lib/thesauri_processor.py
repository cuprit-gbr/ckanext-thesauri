import json
import pickle
from rdflib import Graph, namespace
import time
import urllib.error
import os


class Config:
    """
    Configuration settings for processing and reorganizing thesaurus RDF data.
    """

    root_concept = "http://thesauri.dainst.org/_fe65f286"
    output_format = "json-ld" # Choose from 'turtle', 'xml', 'json-ld'
    input_file = "/tmp/tags_export.json"
    output_file = os.path.join("/tmp", "thesauri")
    request_limit = None # Set to an integer to limit requests for testing, None for unlimited
    


class ThesauriProcessor:
    """
    Harvest RDF data from thesauri.dainst.org, handling parsing with retries and accumulating graphs.
    """

    def __init__(self, root_concept, output_format, output_file, request_limit):
        self.root_concept = root_concept
        self.output_format = output_format
        self.output_file = output_file
        self.request_limit = request_limit
        self.concept_counter = 0
        self.processed_requests = 0
        self.retry_limit = 5
        self.retry_delay = 5
        self.format_suffix_mapping = {"turtle": "ttl", "xml": "xml", "json-ld": "json"}

    def parse_with_retry(self, graph, url):
        """
        Attempts to parse RDF data from a URL with retries on failure.

        Args:
            graph (Graph): An RDFlib Graph object to populate with parsed data.
            url (str): The URL to parse RDF data from.

        Returns:
            bool: True if parsing was successful, False otherwise.
        """
        attempts = 0
        while attempts < self.retry_limit:
            try:
                graph.parse(url)
                return True
            except urllib.error.URLError as e:
                print(
                    f"Network error parsing {url}: {e}. Retrying attempt {attempts + 1}/{self.retry_limit}..."
                )
                attempts += 1
                time.sleep(self.retry_delay)
            except Exception as e:
                print(f"Unexpected error parsing {url}: {e}. Aborting.")
                return False
        return False

    def accumulate_graph(self, url, depths):
        """
        Recursively accumulates RDF graphs starting from a root concept URL.

        Args:
            url (str): The URL of the RDF document to process.
            depths (int): The current depth in the RDF hierarchy.

        Returns:
            Graph: The accumulated RDF graph.
        """
        if (
            self.request_limit is not None
            and self.processed_requests >= self.request_limit
        ):
            print(
                f"Request limit reached ({self.request_limit}). Proceeding with current data."
            )
            return Graph()  # Return an empty graph to stop processing further

        print(f"found {url} at hierarchy depths of {depths}.")
        g = Graph()
        success = self.parse_with_retry(g, url)
        if not success:
            print(f"Failed to load {url} after {self.retry_limit} attempts.")
            return g

        self.concept_counter += 1
        self.processed_requests += 1
        for s, p, o in g.triples((None, namespace.SKOS.narrower, None)):
            narrower_url = o.toPython() + ".ttl"
            g += self.accumulate_graph(narrower_url, depths + 1)
        return g

    def serialize_graph(self):
        """
        Serializes the accumulated RDF graph to the specified format.
        """
        graph = self.accumulate_graph(f"{self.root_concept}.ttl", 0)
        print(f"writing final graph containing {self.concept_counter} concepts")
        graph.serialize(
            destination=f"{self.output_file}.{self.format_suffix_mapping[self.output_format]}",
            format=self.output_format,
        )


class ThesauriReorganizer:
    """
    Reorganizes and serializes thesaurus data into a pickled object and a human-readable JSON file.
    """

    def __init__(self, input_file, output_file):
        self.input_file = input_file
        self.output_file = output_file
        self.parent_relation = "http://www.w3.org/2004/02/skos/core#broader"
        self.child_relations = "http://www.w3.org/2004/02/skos/core#narrower"
        self.top_level_parent_id = "http://thesauri.dainst.org/_fe65f286"
        self.names = "http://www.w3.org/2004/02/skos/core#prefLabel"

        self.exclude_child_terms = set(
            [
                "Geopolitische Einheiten", 
                "Natürliche Prozesse", 
                "Raumbezogene Einheiten", 
                "Ereignisse",
                "Forschungspraktiken",
                "Fiktionale und übernatürliche Wesen",
                "Konzepte des menschlichen Zusammenlebens",
                "Konzepte in den Naturwissenschaften",
                "Theoretische Konzepte",
                "Sprachen",
                "Truppeneinheiten",
                "<nach Typ>",
                "<nach Waren>",
                "<nach Formen>",
                "<nach Beigabenkomplex>",
                "<nach Bestattungsart>",
                "<nach Inhalt>",
                "<nach Technik>",
                "<nach Verzierung>",
                "<nach Verwendung>",
                "<nach Kontext>"
            ]
        )

    def load_data(self):
        """
        Loads the thesaurus data from a JSON file.

        Returns:
            dict: The loaded JSON data.
        """
        with open(self.input_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def find_parents_and_mapping(self, data):
        """
        Identifies parent concepts and establishes a mapping to their IDs.

        Args:
            data (dict): The thesaurus data to process.

        Returns:
            tuple: A tuple containing the flattened data and the mapping dictionary.
        """
        flattened_data = {}
        mapping_dict = {}
        for element in data:
            for e in element.get(self.names, []):
                if e["@language"] == "de" and e["@value"] not in self.exclude_child_terms:
                    de_term = e["@value"]
                    element_id = element["@id"]
                    if element_id not in mapping_dict:  # Ensure unique entries
                        flattened_data[de_term] = []
                        mapping_dict[element_id] = de_term
        return flattened_data, mapping_dict

    def find_relations(self, parent_key, data, childs):
        """
        Recursively finds and adds child concepts to their respective parents.

        Args:
            parent_key (str): The ID of the parent concept.
            data (dict): The thesaurus data to process.
            childs (list): The list of child concepts to update.

        Returns:
            list: The updated list of child concepts.
        """
        for element in data:
            if element["@id"] != parent_key:
                continue
            has_relations = element.get(self.child_relations)
            if has_relations is None:
                for e in element[self.names]:
                    if (
                        e["@language"] == "de"
                        and e["@value"] not in self.exclude_child_terms
                    ):
                        childs.append(e["@value"])
            else:
                for relation in has_relations:
                    self.find_relations(relation["@id"], data, childs)
        return childs

    def flatten_data(self, data):
        """
        Creates a flat dictionary of terms from the thesaurus data.
        Args:
            data (list): The thesaurus data to process, assumed to be a list of dictionaries.
        Returns:
            dict: A flat dictionary with each term as a key.
        """
        flat_dict = {}
        for element in data:
            prefLabels = element.get("http://www.w3.org/2004/02/skos/core#prefLabel", [])
            for label in prefLabels:
                if label.get("@language") == "de":
                    term_value = label.get("@value")
                    flat_dict[term_value] = True  # Value 'True' signifies the presence of the term.
        return flat_dict
    

    def reorganize_and_pickle(self):
        """
        Reorganizes the thesaurus data and saves it as a flat JSON file.
        """
        data = self.load_data()
        flattened_terms = self.flatten_data(data)

        # Convert set to list for JSON serialization
        flattened_terms_list = list(flattened_terms)

        # Serialize to JSON
        with open(f"{self.output_file}.json", "w", encoding="utf-8") as file:
            json.dump(flattened_terms_list, file, ensure_ascii=False, indent=4)

        print(f"Reorganized thesaurus data saved to: {self.output_file}.json")

        # Optionally serialize to Pickle
        with open(f"{self.output_file}.pickle", "wb") as file:
            pickle.dump(flattened_terms_list, file, protocol=pickle.HIGHEST_PROTOCOL)


def main():
    start_time = time.time()  # Start timing

    processor = ThesauriProcessor(
        Config.root_concept,
        Config.output_format,
        "/tmp/thesauri",
        Config.request_limit,
    )
    processor.serialize_graph()

    input_file_for_reorganizer = (
        "/tmp/thesauri.json" 
    )
    reorganizer = ThesauriReorganizer(
        input_file_for_reorganizer,
        "/tmp/thesauri_reorganized", 
    )
    reorganizer.reorganize_and_pickle()

    # Calculate and print the time taken
    end_time = time.time()
    elapsed_time = end_time - start_time
    print(
        f"Thesaurus processing and reorganization completed in {elapsed_time:.2f} seconds."
    )

    # Inform about the saved file paths
    print(
        f"- Harvested RDF from website saved to: {processor.output_file}.{processor.format_suffix_mapping[processor.output_format]}"
    )
    print(
        f"- Reorganized thesaurus data saved to: {reorganizer.output_file}.pickle and {reorganizer.output_file}.json"
    )
    print(
        f"-- The {reorganizer.output_file}.json file can be used to be imported with the second CLI command."
    )

# def main():
#     start_time = time.time()  # Start timing

#     # Path to the existing local JSON file with thesaurus data
#     input_file_for_reorganizer = "/tmp/thesauri.json"
    
#     # Initialize the ThesauriReorganizer with the input and output paths
#     reorganizer = ThesauriReorganizer(
#         input_file_for_reorganizer,
#         "/tmp/thesauri_reorganized",  # Output file path
#     )
    
#     # Directly reorganize and serialize the thesaurus data from the local JSON file
#     reorganizer.reorganize_and_pickle()

#     # Calculate and print the time taken
#     end_time = time.time()
#     elapsed_time = end_time - start_time
#     print(
#         f"Thesaurus reorganization completed in {elapsed_time:.2f} seconds."
#     )

#     # Inform about the saved file paths
#     print(
#         f"- Reorganized thesaurus data saved to: {reorganizer.output_file}.pickle and {reorganizer.output_file}.json"
#     )
#     print(
#         f"-- The {reorganizer.output_file}.json file can be used to be imported with the second CLI command."
#     )

if __name__ == "__main__":
    main()

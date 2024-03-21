from ckan.plugins import toolkit
from ckanext.thesauri_harvester.model.thesauri_model import ThesaurusWord


class ThesaurusController(toolkit.BaseController):
    def list_thesaurus_words(self):
        words = toolkit.get_action("datastore_search")(
            context={"model": toolkit.model, "user": toolkit.c.user},
            data_dict={"resource_id": "thesaurus_words"},
        )

        return toolkit.response.write(words)

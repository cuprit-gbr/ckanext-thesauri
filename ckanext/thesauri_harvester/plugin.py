from flask import Blueprint, request, jsonify  # Import jsonify here
import ckan.model as model
import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
from ckanext.thesauri_harvester.model.thesauri_model import ThesaurusWord
from flask import Blueprint, request
import json
from sqlalchemy.orm import sessionmaker
from ckan.model import Session
import math
from ckanext.thesauri_harvester.cli import get_commands


class ThesauriHarvesterPlugin(plugins.SingletonPlugin, toolkit.DefaultDatasetForm):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IClick)
    plugins.implements(plugins.IActions)
    plugins.implements(plugins.IBlueprint)

    # IConfigurer
    def update_config(self, config_):
        toolkit.add_template_directory(config_, "templates")
        toolkit.add_public_directory(config_, "public")
        toolkit.add_resource("assets", "thesauri_harvester")
        from ckan.model import meta

        meta.metadata.create_all(
            meta.engine, tables=[ThesaurusWord.__table__], checkfirst=True
        )

    # IClick
    def get_commands(self):
        return get_commands()

    # IActions
    def get_actions(self):
        return {"get_thesaurus_words": self.get_thesaurus_words_action}

    @staticmethod
    def get_thesaurus_words_action(context, data_dict):
        search = data_dict.get("search", "")
        page = int(data_dict.get("page", 1))
        per_page = int(data_dict.get("per_page", 10))

        query = Session.query(ThesaurusWord)
        if search:
            query = query.filter(ThesaurusWord.word.ilike('%' + search + '%'))

        total_count = query.count()
        total_pages = math.ceil(total_count / float(per_page))
        words = query.offset((page - 1) * per_page).limit(per_page).all()

        # Determine if there is a next page
        more = page < total_pages

        response = {
            "results": [{"id": word.id, "text": word.word} for word in words],
            "total_count": total_count,
            "total_pages": total_pages,
            "page": page,
            "pagination": {"more": more}
        }
        return response

    # IBlueprint
    def get_blueprint(self):
        blueprint = Blueprint("thesauri_harvester", self.__module__)

        blueprint.add_url_rule(
            "/api/thesauri/words",
            view_func=self.get_thesaurus_words_view,
            methods=["GET"],
        )

        return blueprint

    def get_thesaurus_words_view(self):
        user = toolkit.g.user or toolkit.g.author
        context = {"session": model.Session, "user": user}
        data_dict = {
            "search": request.args.get("search", ""),
            "page": int(request.args.get("page", 1)),
            "per_page": int(request.args.get("per_page", 10)),
        }

        result = toolkit.get_action("get_thesaurus_words")(context, data_dict)
        return jsonify(result)

import click
import json
from sqlalchemy.orm import sessionmaker
from ckan.model.meta import engine
from ckanext.thesauri_harvester.model.thesauri_model import ThesaurusWord
from ckanext.thesauri_harvester.lib.thesauri_processor import (
    main as process_thesaurus_main,
)
from sqlalchemy.exc import IntegrityError

# Setup a sessionmaker
Session = sessionmaker(bind=engine)


@click.group()
def thesauri_harvester():
    """Harvester for thesauri.dainst.org"""
    pass


def populate_database_from_json(filepath):
    """Populate the thesaurus table from a JSON file path, skipping duplicate words."""
    try:
        with open(filepath, "r") as json_file:
            categories = json.load(json_file)
    except (json.JSONDecodeError, IOError) as e:
        click.echo(f"Error: Could not read or decode the JSON file at {filepath}. {e}")
        return

    session = Session()
    try:
        # Flush database table
        session.query(ThesaurusWord).delete()
        session.commit()

        for category, words in categories.items():
            for word in words:
                try:
                    session.add(ThesaurusWord(word=word))
                    session.commit()
                except IntegrityError:
                    session.rollback()  # Rollback the session to continue with the next word
                    click.echo(f"Skipping duplicate word: {word}")

        click.echo("The thesaurus table has been successfully populated.")
    except Exception as e:
        session.rollback()
        click.echo(f"Error populating the thesaurus table: {e}")
    finally:
        session.close()


@thesauri_harvester.command("populate")
@click.argument("json_file_path", type=click.Path(exists=True))
def populate_thesaurus(json_file_path):
    """Flushes the existing thesaurus table and imports new thesaurus words from a JSON file."""
    populate_database_from_json(json_file_path)


@thesauri_harvester.command("harvest")
def process_thesaurus():
    """
    Harvests RDF data from the thesauri.dainst.org, processes it, and saves the output in /tmp directory.
    """
    try:
        process_thesaurus_main()
        click.echo(
            "The thesaurus RDF data has been successfully harvested and processed."
        )
    except Exception as e:
        click.echo(
            f"Error processing the thesaurus RDF data: {e}. Maybe append /tmp/thesauri_reorganized.json to the command?"
        )


@thesauri_harvester.command("harvest-and-process")
def harvest_and_process():
    """
    Combines harvesting and populating the database.
    """
    try:
        process_thesaurus_main()  # Harvest and process RDF data
        output_json_file = (
            "/tmp/thesauri_reorganized.json"  # Adjust this path if necessary
        )
        populate_database_from_json(output_json_file)
        click.echo(
            f"The thesaurus data has been successfully harvested, processed, and populated from {output_json_file}."
        )
    except Exception as e:
        click.echo(
            f"Error during the combined harvesting and processing operation: {e}"
        )


def get_commands():
    return [thesauri_harvester]

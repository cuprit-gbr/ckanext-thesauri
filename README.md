# dai_thesauri_harvester

The `dai_thesauri_harvester` plugin for CKAN enables the harvesting of tags from `[idai.thesauri.de](http://thesauri.dainst.org)` and their addition to a CKAN instance database table. It facilitates the enrichment of dataset metadata by allowing the use of standardized tags from the Digital Archaeological Institute (DAI) Thesaurus. Furthermore, the plugin publishes an API endpoint that is utilized in the package form, enhancing data entry and search capabilities.

## Features

- Harvest tags from `[idai.thesauri.de](http://thesauri.dainst.org)`.
- Populate a CKAN database table with harvested tags.
- Provide an API endpoint for use in dataset forms.
- CLI commands for managing the thesaurus data.

## Usage

### Harvesting and Populating the Thesaurus
To populate the thesaurus table with data from [idai.thesauri.de](http://thesauri.dainst.org) visit

```
ckan -c /etc/ckan/default/production.ini dai_thesauri_harvester
```

### API Endpoint

This plugin adds an API endpoint that can be used on the package form for suggesting tags from the DAI Thesaurus. Documentation for the API endpoint usage can be found at http://<your-ckan-instance>/api/3/action/help_show?name=dai_thesauri_harvester_show.


## Installation

**TODO:** Add any additional install steps to the list below.
   For example installing any non-Python dependencies or adding any required
   config settings.

To install ckanext-thesauri_harvester:

1. Activate your CKAN virtual environment, for example:

     . /usr/lib/ckan/default/bin/activate

2. Clone the source and install it on the virtualenv

    git clone https://github.com//ckanext-thesauri_harvester.git
    cd ckanext-thesauri_harvester
    pip install -e .
	pip install -r requirements.txt

3. Add `thesauri_harvester` to the `ckan.plugins` setting in your CKAN
   config file (by default the config file is located at
   `/etc/ckan/default/ckan.ini`).

4. Restart CKAN. For example if you've deployed CKAN with Apache on Ubuntu:

     sudo service apache2 reload



## Developer installation

To install ckanext-thesauri_harvester for development, activate your CKAN virtualenv and
do:

    git clone https://github.com//ckanext-thesauri_harvester.git
    cd ckanext-thesauri_harvester
    python setup.py develop
    pip install -r dev-requirements.txt



## License

[AGPL](https://www.gnu.org/licenses/agpl-3.0.en.html)

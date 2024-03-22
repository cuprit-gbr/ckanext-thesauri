import pytest
from ckan.plugins import toolkit
import ckanext.thesauri_harvester.plugin as plugin

def plugin_loaded(name):
    """Check if a plugin is loaded."""
    return name in toolkit.config['ckan.plugins']

@pytest.mark.ckan_config("ckan.plugins", "thesauri_harvester")
@pytest.mark.usefixtures("with_plugins")
def test_plugin():
    assert plugin_loaded("thesauri_harvester")

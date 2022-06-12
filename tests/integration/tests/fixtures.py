import pytest
import os
from pytest_ansible_playbook import runner

@pytest.fixture
def ansible_play(request):
   
    # Get required marks, raise exception if not defined or invalid params 
    inventory = request.node.get_closest_marker('ansible_inventory').args[0]
    strategy = request.node.get_closest_marker('ansible_strategy').args[0]
    playbook = request.node.get_closest_marker('ansible_playbook').args[0]

    # Set params for ansible runner
    request.config.option.ansible_playbook_directory = "."
    request.config.option.ansible_playbook_inventory = "inventory.ini"

    # Assign strategy
    os.environ["ANSIBLE_STRATEGY"] = strategy
    
    # Assign inventory (we use symlink)
    os.symlink(inventory, 'inventory.ini.tmp')
    os.rename('inventory.ini.tmp', 'inventory.ini');

    # Test required playbook
    with runner(request, [playbook]):
        yield


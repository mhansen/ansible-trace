import os
import pytest
from pytest_ansible_playbook import runner


@pytest.fixture
def ansible_play(request):

    # Get required marks, raise exception if not defined or invalid params
    inventory = request.node.get_closest_marker('ansible_inventory').args[0]
    strategy = request.node.get_closest_marker('ansible_strategy').args[0]
    playbook = request.node.get_closest_marker('ansible_playbook').args[0]

    # Set params for ansible runner
    request.config.option.ansible_playbook_directory = "."
    request.config.option.ansible_playbook_inventory = inventory

    # Assign strategy
    os.environ["ANSIBLE_STRATEGY"] = strategy

    # Test required playbook
    with runner(request, [playbook]):
        yield

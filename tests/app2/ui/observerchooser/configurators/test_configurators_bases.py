from unittest.mock import Mock

from opendrop.app2.ui.observerchooser.configurators.bases import Configurator


def test_configurator_register():
    checkpoints = []

    my_observer_type = Mock()

    @Configurator.register_configurator(my_observer_type)
    class MyConfigurator(Configurator):
        def __init__(self):
           checkpoints.append(('__init__',))

    my_configurator = Configurator.new_for_type(my_observer_type)

    assert isinstance(my_configurator, MyConfigurator)
    assert checkpoints == [
        ('__init__',)
    ]

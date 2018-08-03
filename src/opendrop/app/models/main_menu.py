from collections import namedtuple

import opendrop

from opendrop.app.models.modifysettings import ModifySettings
from opendrop.app.settings import settings
from opendrop.mvp.Model import Model
from .experiments.ift.experiment_setup import IFTExperimentSetup

About = namedtuple('About', field_names=('program_name', 'version', 'version_name', 'website', 'comments', 'authors'))


class MainMenu(Model):
    ABOUT = About(
        program_name='Opendrop',
        version=opendrop.__version__,
        version_name='Barramundi',
        website='http://www.opencolloids.com',
        comments='OpenDrop is a fully-featured pendant drop tensiometry software, allowing acquisition,'
                 'analysis and fitting of pendant drop profiles to obtain surface and interfacial tension.',
        authors=['John',
                 'Jane',
                 'Jackson',
                 'Jennifer'],)

    def __init__(self):
        super().__init__()

        self.settings = settings

    def new_ift_experiment(self):
        ift_experiment_setup = IFTExperimentSetup()
        return ift_experiment_setup

    def modify_settings(self) -> ModifySettings:
        return ModifySettings(self.settings)

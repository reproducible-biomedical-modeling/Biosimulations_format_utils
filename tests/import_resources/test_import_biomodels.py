""" Tests for importing models from BioModels

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-03-23
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from Biosimulations_utils.api_client import ApiClient, ResponseType
from Biosimulations_utils.data_model import (Identifier, JournalCitation, License, Person, PrimaryResourceMetadata, RemoteFile, Taxon, User)
from Biosimulations_utils.import_resources import biomodels
from Biosimulations_utils.biomodel.data_model import Biomodel
from Biosimulations_utils.simulation.data_model import Simulation
from Biosimulations_utils.visualization.data_model import Visualization
from unittest import mock
try:
    import docker
except ModuleNotFoundError:
    docker = None
import json
import os
import shutil
import tempfile
import unittest


class BioModelsImporterTestCase(unittest.TestCase):
    def setUp(self):
        self.dirname = tempfile.mkdtemp()
        shutil.rmtree(self.dirname)

    def tearDown(self):
        if os.path.isdir(self.dirname):
            shutil.rmtree(self.dirname)

    def test_import_dry_run(self):
        importer = biomodels.BioModelsImporter(exec_simulations=docker is not None,
                                               _max_models=3, _cache_dir=self.dirname, _dry_run=True)
        models, sims, vizs, stats = importer.run()
        self.assertEqual(len(models), 3)

    @unittest.skipIf(os.getenv('CI', '0') in ['1', 'true'], 'CI does not have credentials to log into BioSimulations')
    def test_import_and_post(self):
        # api_client = ApiClient()
        # api_client.login()

        # api_client.exec('delete', '/models', response_type=ResponseType.bytes)
        # models2 = api_client.exec('get', '/models')
        # self.assertEqual(models2, [])

        max_models = 20
        cache_dir = self.dirname
        importer = biomodels.BioModelsImporter(exec_simulations=False, user=User(id='jonrkarr'),
                                               _max_models=max_models, _cache_dir=cache_dir,
                                               _dry_run=True)
        models, sims, vizs, stats = importer.run()
        # self.assertEqual(len(models), max_models)

        # for model in models:
        #     with open(os.path.join('biomodels', model.id + '.json'), 'w') as file:
        #         json.dump(model.to_json(), file)

        # models2_json = api_client.exec('get', '/models')
        # self.assertEqual(len(models2_json), max_models)

        with open('tests/fixtures/biomodels-20.json', 'r') as file:
            models2_json = json.load(file)

        models2 = {}
        for model2_json in models2_json['data']:
            model2 = Biomodel.from_json({'data': model2_json})
            models2[model2.id] = model2

        for model in models[0:20]:
            model2 = models2[model.id]

            model.file = RemoteFile(id=model.file.id)
            model.metadata.image = RemoteFile(id=model.metadata.image.id)
            model.metadata.owner = User(id=model.metadata.owner.id)
            model._metadata = model2._metadata

            self.assertEqual(model, model2)

    def test_import_diverse_set_of_models(self):
        importer = biomodels.BioModelsImporter(exec_simulations=docker is not None,
                                               _max_models=7, _cache_dir=self.dirname, _dry_run=True)
        return_value = {
            'matches': 925,
            'models': [
                {'id': 'BIOMD0000000001', 'name': 'Edelstein1996 - EPSP ACh event'},
                {'id': 'BIOMD0000000002', 'name': 'Edelstein1996 - EPSP ACh species'},
                {'id': 'BIOMD0000000003', 'name': 'Goldbeter1991 - Min Mit Oscil'},
                {
                    'id': 'BIOMD0000000297',  # has time course simulation; tellurium fails on SED-ML interpretation
                    'name': 'Ciliberto2003_Morphogenesis_Checkpoint',
                },
                {
                    'id': 'BIOMD0000000643',  # has time course and steady state simulations
                    'name': 'Musante2017 - Switching behaviour of PP2A inhibition by ARPP-16 - mutual inhibitions',
                },
                {'id': 'BIOMD0000000075', 'name': 'Xu2003 - Phosphoinositide turnover'},  # unable to generate image
                {'id': 'BIOMD0000000596', 'name': 'Philipson2015 - Innate immune response modulated by NLRX1'},
                {'id': 'BIOMD0000000008', 'name': 'Gardner1998 - Cell Cycle Goldbeter'},
                {'id': 'BIOMD0000000009', 'name': 'Huang1996 - Ultrasensitivity in MAPK cascade'},
                {
                    'id': 'BIOMD0000000010',
                    'name': 'Kholodenko2000 - Ultrasensitivity and negative feedback bring oscillations in MAPK cascade',
                },
            ],
        }
        with mock.patch.object(biomodels.BioModelsImporter, 'get_model_batch', return_value=return_value):
            models, sims, vizs, stats = importer.run()
        self.assertEqual(len(models), 7)

        self.assertEqual(models[0].id, 'biomd0000000001')
        self.assertEqual(models[0].metadata.name, 'Edelstein1996 - EPSP ACh event')

        self.assertEqual(models[0].file.name, 'BIOMD0000000001_url.xml')
        self.assertEqual(models[0].file.type, 'application/sbml+xml')
        self.assertGreater(models[0].file.size, 0)

        self.assertEqual(models[0].metadata.image.name, 'BIOMD0000000001_url.png')
        self.assertEqual(models[0].metadata.image.type, 'image/png')
        self.assertGreater(models[0].metadata.image.size, 0)

        self.assertEqual(models[0].metadata.description,
                         ('<div>\n'
                             '  <p>Model of a nicotinic Excitatory Post-Synaptic Potential in a\n'
                             '  Torpedo electric organ. Acetylcholine is not represented\n'
                             '  explicitely, but by an event that changes the constants of\n'
                             '  transition from unliganded to liganded.\xa0\n'
                             '  <br/></p>\n'
                             '</div>'))
        self.assertEqual(models[0].taxon, Taxon(
            id=7787,
            name="Tetronarce californica",
        ))
        self.assertEqual(models[0].metadata.tags, [])
        self.assertEqual(models[0].metadata.references.identifiers, [Identifier(
            namespace="biomodels.db",
            id="BIOMD0000000001",
            url="http://www.ebi.ac.uk/biomodels/BIOMD0000000001"
        )])
        self.assertEqual(models[0].metadata.references.citations, [JournalCitation(
            authors="S J Edelstein, O Schaad, E Henry, D Bertrand & J P Changeux",
            title="A kinetic mechanism for nicotinic acetylcholine receptors based on multiple allosteric transitions.",
            journal="Biological cybernetics",
            volume="75",
            issue=None,
            pages="361-379",
            year=1996,
            doi="10.1007/s004220050302",
        )])
        self.assertEqual(len(models[0].metadata.authors), 5)
        self.assertEqual(models[0].metadata.authors[0], Person(
            last_name="Edelstein",
            first_name="S",
            middle_name="J"
        ))
        self.assertEqual(models[0].metadata.license, License.cc0)

        # verify invalid curves removed
        model = models[3]
        for viz in vizs:
            if viz.id == '{}_viz'.format(model.id):
                break

        layout_vars = []
        for layout_el in viz.layout:
            field_vars = []
            for field in layout_el.data:
                sim_result_vars = []
                for sim_result in field.simulation_results:
                    sim_result_vars.append(sim_result.variable.target)
                field_vars.append(sim_result_vars)
            layout_vars.append(field_vars)

        self.assertEqual(layout_vars, [
            [
                ['urn:sedml:symbol:time'],
                [
                    "/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='BE']",
                    "/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='Cln']",
                    "/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='Sic']",
                ],
            ],
            [
                ['urn:sedml:symbol:time'],
                [
                    "/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='PSwe1M']",
                    "/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='Swe1M']",
                    "/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='Swe1']",
                ],
            ],
        ])

        # verify stats
        self.assertEqual(stats, {
            'models': {
                'total': 7,
                'frameworks': {
                    'non-spatial continuous framework': 7,
                },
                'layouts': 0,
                'taxa': {
                    'Amphibia': 1,
                    'Tetronarce californica': 2,
                    'Schizosaccharomyces pombe': 1,
                    'Mus musculus': 1,
                    'Mus sp.': 1,
                },
                'simulated': 3,
            },
            'sims': {
                'total': 4,
                'time course': 3,
                'one step': 0,
                'steady-state': 1,
            },
            'vizs': {
                'total': 2,
            },
        })

        # verify models can be uploaded to the REST API
        for model in models:
            model.file = RemoteFile(id=model.file.id)
            model.metadata.image = RemoteFile(id=model.metadata.image.id)
            model2 = Biomodel.from_json(model.to_json())
            self.assertEqual(model2, model)
        for sim in sims:
            sim.model = Biomodel(id=sim.model.id)
            if sim.metadata.image:
                sim.metadata.image = RemoteFile(id=sim.metadata.image.id)
            sim2 = Simulation.from_json(sim.to_json())
            self.assertEqual(sim2, sim)
        for viz in vizs:
            if viz.metadata.image:
                viz.metadata.image = RemoteFile(id=viz.metadata.image.id)
            viz2 = Visualization.from_json(viz.to_json())
            self.assertEqual(viz2, viz)

        models_2, sims_2, vizs_2, stats_2 = importer.read_data()
        for model, model_2 in zip(models, models_2):
            self.assertEqual(model_2, model)
        for sim, sim_2 in zip(sims, sims_2):
            self.assertEqual(sim_2, sim)
        for viz, viz_2 in zip(vizs, vizs_2):
            self.assertEqual(viz_2, viz)
        self.assertEqual(stats_2, stats)

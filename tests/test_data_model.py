""" Tests of data model

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-04-01
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from Biosimulations_format_utils.data_model import (Format, Identifier, JournalReference,
                                                    License, OntologyTerm, Person, RemoteFile, Taxon, Type)
from Biosimulations_format_utils.model.data_model import Model, ModelParameter, Variable
import json
import requests
import unittest


class DataModelTestCase(unittest.TestCase):
    def test_Format(self):
        format = Format(name='SBML', version='L3V2', edam_id='format_2585', url='http://sbml.org')
        self.assertEqual(Format.from_json(format.to_json()), format)

    def test_Identifier(self):
        id = Identifier(namespace='biomodels.db', id='BIOMD0000000924')
        self.assertEqual(Identifier.from_json(id.to_json()), id)

        self.assertEqual(Identifier.sort_key(id), (id.namespace, id.id))

    def test_JournalReference(self):
        ref = JournalReference(authors='John Doe and Jane Doe', title='title', journal='journal',
                               volume=10, num=3, pages='1-10', year=2020, doi='10.1016/XXXX')
        self.assertEqual(JournalReference.from_json(ref.to_json()), ref)
        self.assertEqual(JournalReference.sort_key(ref), (ref.authors, ref.title,
                                                          ref.journal, ref.volume, ref.num, ref.pages, ref.year, ref.doi))

    def test_OntologyTerm(self):
        term = OntologyTerm(ontology='KISAO', id='0000497', name='KLU',
                            description='KLU is a software package and an algorithm ...',
                            iri='http://www.biomodels.net/kisao/KISAO#KISAO_0000497')
        self.assertEqual(OntologyTerm.from_json(term.to_json()), term)

    def test_Person(self):
        person = Person(first_name='John', middle_name='C', last_name='Doe')
        self.assertEqual(Person.from_json(person.to_json()), person)
        self.assertEqual(Person.sort_key(person), (person.last_name, person.first_name, person.middle_name))

    def test_RemoteFile(self):
        file = RemoteFile(name='model.xml', type='application/sbml+xml', size=1000)
        self.assertEqual(RemoteFile.from_json(file.to_json()), file)

    def test_Taxon(self):
        taxon = Taxon(id=9606, name='Homo sapiens')
        self.assertEqual(Taxon.from_json(taxon.to_json()), taxon)


class ApiConsistencyTestCase(unittest.TestCase):
    SPEC = 'https://api.biosimulations.dev/openapi.json'

    @classmethod
    def setUpClass(cls):
        response = requests.get(cls.SPEC)
        response.raise_for_status()
        cls.api_schemas = response.json()['components']['schemas']

    @unittest.expectedFailure()
    def test_model(self):
        model = Model(
            id='model_1',
            name='model 1',
            file=RemoteFile(name='model.xml', type='application/sbml+xml'),
            image=RemoteFile(name='model.png', type='image/png'),
            description='description',
            format=Format(name='SBML', version='L3V2', edam_id='format_2585', url='http://sbml.org'),
            framework=OntologyTerm(ontology='KISAO', id='0000497', name='KLU',
                                   description='KLU is a software package and an algorithm ...',
                                   iri='http://www.biomodels.net/kisao/KISAO#KISAO_0000497'),
            taxon=Taxon(id=9606, name='Homo sapiens'),
            tags=['a', 'b', 'c'],
            identifiers=[Identifier(namespace='biomodels.db', id='BIOMD0000000924')],
            references=[
                JournalReference(authors='John Doe and Jane Doe', title='title', journal='journal',
                                 volume=10, num=3, pages='1-10', year=2020, doi='10.1016/XXXX'),
            ],
            authors=[
                Person(first_name='John', middle_name='C', last_name='Doe'),
                Person(first_name='Jane', middle_name='D', last_name='Doe'),
            ],
            license=License.cc0,
            parameters=[ModelParameter(id='k_1', type=Type.float, identifiers=[Identifier(namespace='a', id='x')])],
            variables=[Variable(id='species_1', type=Type.float, identifiers=[Identifier(namespace='a', id='x')])],
        )
        py = model.to_json()

        api = {}
        for schema in self.api_schemas['Model']['allOf']:
            for key, val in schema['properties'].items():
                api[key] = val

        errors = self.get_differences_from_api(py, api)
        if errors:
            raise Exception('Data model for `Model` is not consistent with API:\n  Model:\n    ' + '\n    '.join(errors))

    @unittest.expectedFailure()
    def test_sim(self):
        with open('tests/fixtures/simulation.json', 'rb') as file:
            py = json.load(file)

        api = {}
        for schema in self.api_schemas['Simulation']['allOf']:
            for key, val in schema['properties'].items():
                api[key] = val

        errors = self.get_differences_from_api(py, api)
        if errors:
            raise Exception('Data model for `Simulation` is not consistent with API:\n  Simulation:\n    ' + '\n    '.join(errors))

    def get_differences_from_api(self, py, api, path=''):
        errors = []

        for key, val in py.items():
            if key not in api:
                errors.append('{}: not in API'.format(path + key))
            else:
                if isinstance(val, list):
                    if isinstance(val[0], dict):
                        if 'items' not in api[key]:
                            errors.append('{}: API does not use an array'.format(path + key))
                        elif 'properties' not in api[key]['items']:
                            errors.append('{}'.format(path + key))
                            errors.append('  {}: API does not use an array of dictionaries'.format(path + key[0:-1]))
                        else:
                            prop_errors = self.get_differences_from_api(val[0], api[key]['items']['properties'], path=path + '    ')
                            if prop_errors:
                                errors.append('{}'.format(path + key))
                                errors.append('  {}'.format(path + key[0:-1]))
                                errors.extend(prop_errors)
                elif isinstance(val, dict):
                    if 'properties' not in api[key]:
                        errors.append('{}: API does not use a dictionary'.format(path + key))
                    else:
                        prop_errors = self.get_differences_from_api(val, api[key]['properties'], path=path + '  ')
                        if prop_errors:
                            errors.append('{}'.format(path + key))
                            errors.extend(prop_errors)

        return errors

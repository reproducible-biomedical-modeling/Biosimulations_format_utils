""" Test of SED-ML utilities

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-03-20
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from Biosimulations_format_utils.data_model import Format
from Biosimulations_format_utils.model import ModelFormat
from Biosimulations_format_utils.model.data_model import Model, ModelVariable
from Biosimulations_format_utils.sim import SimFormat, write_sim, read_sim, sedml
from Biosimulations_format_utils.sim.core import SimIoError, SimIoWarning
from Biosimulations_format_utils.sim.data_model import TimecourseSimulation
import json
import libsedml
import os
import shutil
import tempfile
import unittest


class WriteSedMlTestCase(unittest.TestCase):
    def setUp(self):
        self.dirname = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.dirname)

    def test_gen_sedml(self):
        model_vars = [
            ModelVariable(id='species_1', target="/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='species_1']"),
            ModelVariable(id='species_2', target="/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='species_2']"),
        ]
        with open('tests/fixtures/simulation.json', 'rb') as file:
            sim = TimecourseSimulation.from_json(json.load(file))
        model_filename = os.path.join(self.dirname, 'model.sbml.xml')
        sim_filename = os.path.join(self.dirname, 'simulation.sed-ml.xml')
        write_sim(model_vars, sim, model_filename, sim_filename,
                  SimFormat.sedml, level=1, version=3)

        sims_2 = read_sim(
            sim_filename, ModelFormat.sbml, SimFormat.sedml)
        self.assertEqual(len(sims_2), 1)
        sim_2 = sims_2[0]
        self.assertEqual(
            set(v.id for v in sim_2.model.variables),
            set(v.id for v in model_vars))
        self.assertEqual(sim_2.model.file.name, model_filename)
        sim_2.model.file = None
        sim_2.model.variables = []
        self.assertEqual(sim_2, sim)
        self.assertEqual(sim_2.format.version, 'L1V3')

        with self.assertRaisesRegex(NotImplementedError, 'not supported'):
            read_sim(None, ModelFormat.sbml, SimFormat.sessl)

        with self.assertRaisesRegex(NotImplementedError, 'not supported'):
            read_sim(None, ModelFormat.cellml, SimFormat.sedml)

    def test_gen_sedml_errors(self):
        # Other versions/levels of SED-ML are not supported
        sim = TimecourseSimulation(
            model=Model(
                format=Format(
                    name='SBML'
                )
            ),
            format=Format(
                name='SED-ML',
                version='L1V2',
            )
        )
        with self.assertRaisesRegex(ValueError, 'Format must be SED-ML'):
            write_sim(None, sim, None, None, SimFormat.sedml, level=1, version=3)

        # other simulation experiments formats (e.g., SESSL) are not supported
        sim = TimecourseSimulation(
            model=Model(
                format=Format(
                    name='SBML'
                )
            ),
            format=Format(
                name='SESSL'
            )
        )
        with self.assertRaisesRegex(NotImplementedError, 'is not supported'):
            write_sim(None, sim, None, None, SimFormat.sessl, level=1, version=3)
        with self.assertRaisesRegex(ValueError, 'Format must be SED-ML'):
            write_sim(None, sim, None, None, SimFormat.sedml, level=1, version=3)

        # other simulation experiments formats (e.g., SESSL) are not supported
        sim = TimecourseSimulation(
            model=Model(
                format=Format(
                    name='CellML'
                )
            ),
            format=Format(
                name='SED-ML',
                version='L1V3',
            ),
        )
        with self.assertRaisesRegex(NotImplementedError, 'is not supported'):
            write_sim(None, sim, 'model.sbml.xml', None, SimFormat.sedml, level=1, version=3)

    def test__get_obj_annotation(self):
        reader = sedml.SedMlSimReader()

        doc = libsedml.SedDocument()
        self.assertEqual(reader._get_obj_annotation(doc), [])

        doc.setAnnotation('<annotation></annotation>')
        self.assertEqual(reader._get_obj_annotation(doc), [])

        doc.setAnnotation('<annotation><rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"></rdf:RDF></annotation>')
        self.assertEqual(reader._get_obj_annotation(doc), [])

        doc.setAnnotation(
            '<annotation><rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">'
            '<rdf:Description></rdf:Description>'
            '</rdf:RDF></annotation>')
        self.assertEqual(reader._get_obj_annotation(doc), [])

    def test__call_sedml_error(self):
        doc = libsedml.SedDocument()
        with self.assertRaisesRegex(ValueError, 'libsedml error:'):
            sedml.SedMlSimWriter._call_libsedml_method(doc, doc, 'setAnnotation', '<rdf')

        with self.assertRaisesRegex(SimIoError, 'libsedml error'):
            sedml.SedMlSimReader().run('non-existant-file')

    def test_read_with_multiple_models_and_sims_and_unsupported_task(self):
        filename = 'tests/fixtures/Simon2019-with-multiple-models-and-sims.sedml'
        with self.assertWarnsRegex(SimIoWarning, 'is not supported'):
            read_sim(filename, ModelFormat.sbml, SimFormat.sedml)

    def test_read_with_unsupported_simulation(self):
        filename = 'tests/fixtures/Simon2019-with-one-step-sim.sedml'
        with self.assertRaisesRegex(SimIoError, 'Unsupported simulation type'):
            read_sim(filename, ModelFormat.sbml, SimFormat.sedml)

    def test_read_biomodels_sims(self):
        sims = read_sim('tests/fixtures/Simon2019.sedml', ModelFormat.sbml, SimFormat.sedml)
        self.assertEqual(len(sims), 1)
        sim = sims[0]
        self.assertEqual(sim.model_parameter_changes, [])
        self.assertEqual(sim.start_time, 0.)
        self.assertEqual(sim.output_start_time, 0.)
        self.assertEqual(sim.end_time, 1.)
        self.assertEqual(sim.num_time_points, 100)
        self.assertEqual(sim.algorithm.id, 'KISAO:0000019')
        self.assertEqual(sim.algorithm_parameter_changes, [])

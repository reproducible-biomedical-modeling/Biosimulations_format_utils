""" Utilities for validate containerized simulators

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-04-13
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from Biosimulations_utils import config
from Biosimulations_utils.archive import read_archive
from Biosimulations_utils.archive.data_model import ArchiveFormat
from Biosimulations_utils.archive.exec import gen_archive_for_sim, exec_archive
from Biosimulations_utils.biomodel import read_biomodel
from Biosimulations_utils.biomodel.data_model import BiomodelingFramework, BiomodelFormat, BiomodelParameter
from Biosimulations_utils.data_model import (JournalCitation, License, OntologyTerm, Person,
                                             PrimaryResourceMetadata, ResourceMetadata, ResourceReferences)
from Biosimulations_utils.simulation import read_simulation
from Biosimulations_utils.simulation.data_model import (
    TimecourseSimulation, Algorithm, AlgorithmParameter, ParameterChange, SimulationFormat)
from Biosimulations_utils.simulator.data_model import Simulator
import copy
import datetime
import dateutil.tz
import enum
import glob
import json
import os
import numpy.testing
import pandas
import shutil
import tempfile

__all__ = ['TestCaseType', 'TestCase', 'TestCaseException', 'SimulatorValidator']


class TestCaseType(int, enum.Enum):
    """ Type of test case """
    archive = 1
    biomodel = 2


class TestCase(object):
    """ An example archive to validate simulators

    Attributes:
        id (:obj:`str`): id
        filename (:obj:`str`): path to archive
        type (:obj:`TestCaseType`): type of test case
        modeling_framework (:obj:`BiomodelingFramework`): modeling framework
        model_format (:obj:`BiomodelFormat`): model format
        simulation_format (:obj:`SimulationFormat`): simulation format
        archive_format (:obj:`ArchiveFormat`): archive format
    """

    def __init__(self, id, filename, type, modeling_framework, model_format, simulation_format, archive_format):
        """
        Args:
            id (:obj:`str`): id
            filename (:obj:`str`): path to archive
            type (:obj:`TestCaseType`): type of test case
            modeling_framework (:obj:`BiomodelingFramework`): modeling framework
            model_format (:obj:`BiomodelFormat`): model format
            simulation_format (:obj:`SimulationFormat`): simulation format
            archive_format (:obj:`ArchiveFormat`): archive format
        """
        self.id = id
        self.filename = filename
        self.type = type
        self.modeling_framework = modeling_framework
        self.model_format = model_format
        self.simulation_format = simulation_format
        self.archive_format = archive_format

    def __eq__(self, other):
        """ Determine if two test cases are semantically equal

        Args:
            other (:obj:`TestCase`): other test case

        Returns:
            :obj:`bool`
        """
        return other.__class__ == self.__class__ \
            and self.id == other.id \
            and self.filename == other.filename \
            and self.type == other.type \
            and self.modeling_framework == other.modeling_framework \
            and self.model_format == other.model_format \
            and self.simulation_format == other.simulation_format \
            and self.archive_format == other.archive_format

    def to_json(self):
        """ Export to JSON

        Returns:
            :obj:`dict`
        """
        return {
            'id': self.id,
            'filename': self.filename,
            'type': self.type.name if self.type else None,
            'modeling-framework': self.modeling_framework.name if self.modeling_framework else None,
            'model-format': self.model_format.name if self.model_format else None,
            'simulation-format': self.simulation_format.name if self.simulation_format else None,
            'archive-format': self.archive_format.name if self.archive_format else None,
        }

    @classmethod
    def from_json(cls, val):
        """ Create a test case from JSON

        Args:
            val (:obj:`dict`)

        Returns:
            :obj:`TestCase`
        """
        return cls(
            id=val.get('id', None),
            filename=val.get('filename', None),
            type=TestCaseType[val.get('type')] if val.get('type', None) else None,
            modeling_framework=BiomodelingFramework[val.get('modeling-framework')] if val.get('modeling-framework', None) else None,
            model_format=BiomodelFormat[val.get('model-format')] if val.get('model-format', None) else None,
            simulation_format=SimulationFormat[val.get('simulation-format')] if val.get('simulation-format', None) else None,
            archive_format=ArchiveFormat[val.get('archive-format')] if val.get('archive-format', None) else None,
        )


class TestCaseException(object):
    """ An exception of a test case

    Attributes:
        test_case (:obj:`TestCase`): test case
        exception (:obj:`Exception`): exception
    """

    def __init__(self, test_case, exception):
        """
        Args:
            test_case (:obj:`TestCase`): test case
            exception (:obj:`Exception`): exception
        """
        self.test_case = test_case
        self.exception = exception


class SimulatorValidator(object):
    """ Validate that a Docker image for a simulator implements the BioSimulations simulator interface by
    checking that the image produces the correct outputs for one of more test cases (e.g., COMBINE archive)

    Attributes:
        test_cases (:obj:`list` of :obj:`TestCase`): test cases
    """

    def __init__(self):
        dirname = config.combine_test_suite.dirname
        self.test_cases = self.get_test_cases(dirname)

    def get_test_cases(self, dirname):
        """ Collect test cases from a directory

        Args:
            dirname (:obj:`str`): path to test cases and metadata about each test case (one JSON file per test case)

        Returns:
            test_cases (:obj:`list` of :obj:`TestCase`): test cases
        """
        test_cases = []

        for md_filename in glob.glob(os.path.join(dirname, '*.json')):
            with open(md_filename, 'r') as md_file:
                test_case = TestCase.from_json(json.load(md_file))
                test_case.filename = os.path.join(dirname, test_case.filename)
                test_cases.append(test_case)

        return test_cases

    def run(self, docker_image_url, properties, test_case_ids=None):
        """ Validate that a Docker image for a simulator implements the BioSimulations simulator interface by
        checking that the image produces the correct outputs for test cases (e.g., COMBINE archive)

        Args:
            docker_image_url (:obj:`str`): URL for Docker image id of simulator
            properties (:obj:`str` or :obj:`dict`): path to the properties of the simulator or the properties of the simulator
            test_case_ids (:obj:`list` of :obj:`str`, optional): List of ids of test cases to verify. If :obj:`test_case_ids`
                is none, all test cases are verified.

        Returns:
            :obj:`list` :obj:`TestCase`: valid test cases
            :obj:`list` :obj:`TestCaseException`: invalid test cases
        """
        if isinstance(properties, str):
            with open(properties, 'r') as file:
                properties = json.load(file)
        simulator = Simulator.from_json(properties)

        valid_test_cases = []
        test_case_exceptions = []
        skipped_test_cases = []
        for test_case in self.test_cases:
            if test_case_ids is not None and test_case.id not in test_case_ids:
                skipped_test_cases.append(test_case)
                continue

            for algorithm in simulator.algorithms:
                case_supports_modeling_framework = False
                for modeling_framework in algorithm.modeling_frameworks:
                    if modeling_framework.ontology == test_case.modeling_framework.value.ontology and \
                       modeling_framework.id == test_case.modeling_framework.value.id:
                        case_supports_modeling_framework = True
                        break

                case_supports_model_format = False
                for model_format in algorithm.model_formats:
                    if model_format.id == test_case.model_format.value.id:
                        case_supports_model_format = True
                        break

                case_supports_simulation_format = False
                for simulation_format in algorithm.simulation_formats:
                    if simulation_format.id == test_case.simulation_format.value.id:
                        case_supports_simulation_format = True
                        break

                case_supports_archive_format = False
                for archive_format in algorithm.archive_formats:
                    if archive_format.id == test_case.archive_format.value.id:
                        case_supports_archive_format = True
                        break

            use_test_case = case_supports_modeling_framework \
                and case_supports_model_format \
                and case_supports_simulation_format \
                and case_supports_archive_format

            if use_test_case:
                if test_case.type == TestCaseType.biomodel:
                    model_filename = test_case.filename
                    model = self._gen_example_model(model_filename)
                    simulation = self._gen_example_simulation(model)
                    simulation.model_parameter_changes = [
                        ParameterChange(parameter=BiomodelParameter(target=param.target), value=0.)
                        for param in model.parameters if param.group == 'Initial species amounts/concentrations'
                    ]
                    _, archive_filename = self._gen_example_archive(model_filename, simulation)
                else:
                    archive_filename = test_case.filename

                try:
                    self._validate_test_case(test_case, archive_filename, docker_image_url)
                    valid_test_cases.append(test_case)
                except Exception as exception:
                    test_case_exceptions.append(TestCaseException(test_case, exception))
            else:
                skipped_test_cases.append(test_case)

        print('Passed {} test cases:\n  {}'.format(len(valid_test_cases), '\n  '.join(
            case.filename for case in valid_test_cases)))
        print('Failed {} test cases:\n  {}'.format(len(test_case_exceptions), '\n  '.join(
            '{}\n    {}'.format(test_case_exception.test_case.filename, str(test_case_exception.exception))
            for test_case_exception in test_case_exceptions)))
        print('Skipped {} test cases:\n  {}'.format(len(skipped_test_cases), '\n  '.join(
            case.filename for case in skipped_test_cases)))
        return valid_test_cases, test_case_exceptions, skipped_test_cases

    def _gen_example_model(self, model_filename):
        """ Generate an example model

        Args:
            model_filename (:obj:`str`): path to example model

        Returns:
            :obj:`Biomodel`: example model
        """
        model = read_biomodel(model_filename, format=BiomodelFormat.sbml)
        model.file.name = 'BIOMD0000000297_url.xml'
        model.metadata.description = 'Description of model 1'
        model.metadata.tags = ['tag-model-a', 'tag-model-b', 'tag-model-c']
        model.metadata.references = ResourceReferences(
            citations=[
                JournalCitation(authors='John Doe and Jane Doe', title='title', journal='journal',
                                volume=10, issue=3, pages='1-10', year=2020, doi='10.1016/XXXX'),
            ]
        )
        model.metadata.authors = [
            Person(first_name='Jack', middle_name='A', last_name='Doe'),
            Person(first_name='Jill', middle_name='B', last_name='Doe'),
        ]
        model.metadata.license = License.cc0
        model._metadata.created = datetime.datetime.utcnow().replace(microsecond=0).replace(tzinfo=dateutil.tz.UTC)
        model._metadata.updated = datetime.datetime.utcnow().replace(microsecond=0).replace(tzinfo=dateutil.tz.UTC)
        return model

    def _gen_example_simulation(self, model):
        """ Generate an example simulation

        Args:
            model (:obj:`Biomodel`): model

        Returns:
            :obj:`Simulation`: example simulation
        """
        simulation = TimecourseSimulation(
            id='simulation_1',
            model=model,
            model_parameter_changes=[
            ],
            start_time=0.,
            output_start_time=0.,
            end_time=10.,
            num_time_points=100,
            algorithm=Algorithm(
                kisao_term=OntologyTerm(
                    ontology='KISAO',
                    id='0000019',
                    name='CVODE',
                ),
                id='CVODE',
                name='C-language Variable-coefficient Ordinary Differential Equation solver',
            ),
            algorithm_parameter_changes=[
                ParameterChange(
                    parameter=AlgorithmParameter(
                        kisao_term=OntologyTerm(
                            ontology='KISAO',
                            id='0000209',
                        ),
                        id='rel_tol',
                        name='Relative tolerance',
                    ),
                    value=1e-5,
                ),
                ParameterChange(
                    parameter=AlgorithmParameter(
                        kisao_term=OntologyTerm(
                            ontology='KISAO',
                            id='0000211',
                        ),
                        id='abs_tol',
                        name='Absolute tolerance',
                    ),
                    value=1e-11,
                ),
            ],
            format=copy.copy(SimulationFormat.sedml.value),
            metadata=PrimaryResourceMetadata(
                name='simulation 1',
                description='Description of simulation 1',
                tags=['tag-simulation-a', 'tag-simulation-b', 'tag-simulation-c'],
                references=ResourceReferences(
                    citations=[
                        JournalCitation(authors='John Doe and Jane Doe', title='title', journal='journal',
                                        volume=10, issue=3, pages='1-10', year=2020, doi='10.1016/XXXX'),
                    ]
                ),
                authors=[
                    Person(first_name='John', middle_name='C', last_name='Doe'),
                    Person(first_name='Jane', middle_name='D', last_name='Doe'),
                ],
                license=License.cc0,
            ),
            _metadata=ResourceMetadata(
                created=datetime.datetime.utcnow().replace(microsecond=0).replace(tzinfo=dateutil.tz.UTC),
                updated=datetime.datetime.utcnow().replace(microsecond=0).replace(tzinfo=dateutil.tz.UTC),
            ),
        )
        simulation.format.version = 'L1V3'

        return simulation

    def _gen_example_archive(self, model_filename, simulation):
        """ Encode a simulation into SED-ML and generate an example COMBINE archive for it

        Args:
            model_filename (:obj:`str`): path to example model
            simulation (:obj:`Simulation`): simulation of model

        Returns:
            :obj:`tuple`:

                * :obj:`Archive`: properties of the archive
                * :obj:`str`: path to archive
        """
        fid, archive_filename = tempfile.mkstemp(suffix='.omex')
        os.close(fid)
        archive = gen_archive_for_sim(model_filename, simulation, archive_filename)
        return (archive, archive_filename)

    def _validate_test_case(self, test_case, archive_filename, docker_image_url):
        """ Validate that a simulator correctly produces the outputs for a test case

        Args:
            test_case (:obj:`TestCase`): test case
            archive_filename (:obj:`str`): path to archive
            docker_image_url (:obj:`str`): URL for Docker image of simulator
        """
        # create output directory
        out_dir = tempfile.mkdtemp()

        # execute archive
        exec_archive(archive_filename, docker_image_url, out_dir)

        # check output
        self._assert_archive_output_valid(test_case, archive_filename, out_dir)

        # cleanup
        shutil.rmtree(out_dir)

    def _assert_archive_output_valid(self, test_case, archive_filename, out_dir):
        """ Validate that the outputs of an archive were correctly generated

        Args:
            test_case (:obj:`TestCase`): test case
            archive_filename (:obj:`str`): path to archive
            out_dir (:obj:`str`): directory which contains the simulation results

        Raises:
            :obj:`AssertionError`: simulator did not generate the specified outputs
        """
        # read archive and unpack to temporary directory
        archive_dir = tempfile.mkdtemp()
        archive = read_archive(archive_filename, archive_dir)

        # validate that outputs were created
        for file in archive.files:
            if file.format.spec_url == test_case.simulation_format.value.spec_url:
                simulation_file_name = os.path.join(archive_dir, file.filename)
                simulations, _ = read_simulation(simulation_file_name)
                for simulation in simulations:
                    simulation_out_dir = os.path.join(out_dir, os.path.splitext(file.filename)[0])
                    simulation_report_filename = os.path.join(simulation_out_dir, simulation.id + '.csv')
                    assert os.path.isdir(simulation_out_dir), "Output directory {} was not created".format(simulation_out_dir)
                    assert os.path.isfile(simulation_report_filename), "Report {} was not created".format(simulation_report_filename)

                    results_data_frame = pandas.read_csv(simulation_report_filename)

                    numpy.testing.assert_array_almost_equal(
                        results_data_frame['time'],
                        numpy.linspace(simulation.output_start_time, simulation.end_time, simulation.num_time_points + 1),
                    )

                    assert set(results_data_frame.columns.to_list()) == set([var.id for var in simulation.model.variables] + ['time'])

        # cleanup
        shutil.rmtree(archive_dir)

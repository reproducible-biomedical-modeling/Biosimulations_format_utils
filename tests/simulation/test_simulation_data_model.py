""" Tests of data model for simulations

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-04-01
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from Biosimulations_format_utils.data_model import Format, JournalReference, License, OntologyTerm, Person, RemoteFile, Type
from Biosimulations_format_utils.biomodel.data_model import Biomodel, BiomodelParameter, BiomodelVariable
from Biosimulations_format_utils.biomodel.sbml import BiomodelingFramework
from Biosimulations_format_utils.simulation.data_model import (
    Simulation, TimecourseSimulation, SteadyStateSimulation, Simulator, Algorithm, AlgorithmParameter, ParameterChange,
    SimulationResult)
import unittest


class SimulationDataModelTestCase(unittest.TestCase):
    def test_TimecourseSimulation(self):
        sim = TimecourseSimulation(
            id='model_1',
            name='model 1',
            image=RemoteFile(name='model.png', type='image/png'),
            description='description',
            tags=['a', 'b', 'c'],
            references=[
                JournalReference(authors='John Doe and Jane Doe', title='title', journal='journal',
                                 volume=10, issue=3, pages='1-10', year=2020, doi='10.1016/XXXX'),
            ],
            authors=[
                Person(first_name='John', middle_name='C', last_name='Doe'),
                Person(first_name='Jane', middle_name='D', last_name='Doe'),
            ],
            license=License.cc0,
            format=Format(name='SBML', version='L3V2', edam_id='format_2585', url='http://sbml.org'),
            model=Biomodel(id='model_1', name='model 1'),
            model_parameter_changes=[
                ParameterChange(parameter=BiomodelParameter(id='param_1', name='param 1', type=Type.float, value=3.5),
                                value=5.3),
            ],
            start_time=0.,
            output_start_time=1.,
            end_time=10.,
            num_time_points=100,
            algorithm=Algorithm(id='00001', name='integrator', kisao_term=OntologyTerm(ontology='KISAO', id='00001'), parameters=[
                AlgorithmParameter(id='param_1', name='param 1', type=Type.float, value=1.2,
                                   recommended_range=[0.12, 12.], kisao_term=OntologyTerm(ontology='KISAO', id='00001')),
            ]),
            algorithm_parameter_changes=[
                ParameterChange(parameter=AlgorithmParameter(id='param_1', name='param 1', type=Type.float,
                                                             value=1.2, recommended_range=[0.12, 12.],
                                                             kisao_term=OntologyTerm(ontology='KISAO', id='00001')),
                                value=2.1),
            ]
        )
        self.assertEqual(TimecourseSimulation.from_json(sim.to_json()), sim)
        self.assertEqual(Simulation.from_json(sim.to_json()), sim)

    def test_SteadyStateSimulation(self):
        sim = SteadyStateSimulation(
            id='model_1',
            name='model 1',
            image=RemoteFile(name='model.png', type='image/png'),
            description='description',
            tags=['a', 'b', 'c'],
            references=[
                JournalReference(authors='John Doe and Jane Doe', title='title', journal='journal',
                                 volume=10, issue=3, pages='1-10', year=2020, doi='10.1016/XXXX'),
            ],
            authors=[
                Person(first_name='John', middle_name='C', last_name='Doe'),
                Person(first_name='Jane', middle_name='D', last_name='Doe'),
            ],
            license=License.cc0,
            format=Format(name='SBML', version='L3V2', edam_id='format_2585', url='http://sbml.org'),
            model=Biomodel(id='model_1', name='model 1'),
            model_parameter_changes=[
                ParameterChange(parameter=BiomodelParameter(id='param_1', name='param 1', type=Type.float, value=3.5),
                                value=5.3),
            ],
            algorithm=Algorithm(id='00001', name='integrator', kisao_term=OntologyTerm(ontology='KISAO', id='00001'), parameters=[
                AlgorithmParameter(id='param_1', name='param 1', type=Type.float, value=1.2,
                                   recommended_range=[0.12, 12.], kisao_term=OntologyTerm(ontology='KISAO', id='00001')),
            ]),
            algorithm_parameter_changes=[
                ParameterChange(parameter=AlgorithmParameter(id='param_1',
                                                             name='param 1',
                                                             type=Type.float,
                                                             value=1.2,
                                                             recommended_range=[0.12, 12.],
                                                             kisao_term=OntologyTerm(ontology='KISAO', id='00001')),
                                value=2.1),
            ]
        )
        self.assertEqual(SteadyStateSimulation.from_json(sim.to_json()), sim)
        self.assertEqual(Simulation.from_json(sim.to_json()), sim)

    def test_Simulator(self):
        simulator = Simulator(
            id='tellurium',
            name='tellurium',
            version='2.4.1',
            description='description of tellurium',
            url='http://tellurium.analogmachine.org/',
            docker_hub_image_id='crbm/biosimulations_tellurium:2.4.1',
            algorithms=[
                Algorithm(
                    id='00001',
                    name='integrator',
                    kisao_term=OntologyTerm(ontology='KISAO', id='00001'),
                    ontology_terms=[
                        OntologyTerm(ontology='KISAO', id='00002'),
                        OntologyTerm(ontology='KISAO', id='00003'),
                    ],
                    modeling_frameworks=[
                        BiomodelingFramework.logical.value,
                        BiomodelingFramework.flux_balance.value,
                    ],
                    model_formats=[
                        Format(name='SBML', version='L3V2', edam_id='format_2585', url='http://sbml.org'),
                    ],
                    parameters=[
                        AlgorithmParameter(id='param_1',
                                           name='param 1',
                                           type=Type.float,
                                           value=1.2,
                                           recommended_range=[0.12, 12.],
                                           kisao_term=OntologyTerm(ontology='KISAO', id='00001')),
                    ],
                )
            ],
        )
        self.assertEqual(Simulator.from_json(simulator.to_json()), simulator)

    def test_Algorithm(self):
        alg = Algorithm(
            id='00001',
            name='integrator',
            kisao_term=OntologyTerm(ontology='KISAO', id='00001'),
            ontology_terms=[
                OntologyTerm(ontology='KISAO', id='00002'),
                OntologyTerm(ontology='KISAO', id='00003'),
            ],
            modeling_frameworks=[
                BiomodelingFramework.logical.value,
                BiomodelingFramework.flux_balance.value,
            ],
            model_formats=[
                Format(name='SBML', version='L3V2', edam_id='format_2585', url='http://sbml.org'),
            ],
            parameters=[
                AlgorithmParameter(id='param_1',
                                   name='param 1',
                                   type=Type.float,
                                   value=1.2,
                                   recommended_range=[0.12, 12.],
                                   kisao_term=OntologyTerm(ontology='KISAO', id='00001')),
            ],
        )
        self.assertEqual(Algorithm.from_json(alg.to_json()), alg)
        self.assertEqual(Algorithm.sort_key(alg), (
            '00001',
            'integrator',
            ('KISAO', '00001', None, None, None),
            (
                ('KISAO', '00002', None, None, None),
                ('KISAO', '00003', None, None, None),
            ),
            (
                ('SBO', '0000234', 'logical framework',
                 ('Modelling approach, pioneered by Rene Thomas and Stuart Kaufman, where the '
                  'evolution of a system is described by the transitions between discrete activity '
                  'states of "genes" that control each other.'),
                 'http://biomodels.net/SBO/SBO_0000234',
                 ),
                ('SBO', '0000624', 'flux balance framework',
                 ('Modelling approach, typically used for metabolic models, where the flow '
                  'of metabolites (flux) through a network can be calculated. This approach '
                  'will generally produce a set of solutions (solution space), which may be '
                  'reduced using objective functions and constraints on individual fluxes.'),
                 'http://biomodels.net/SBO/SBO_0000624',
                 ),
            ),
            (
                (None, 'SBML', 'L3V2', 'format_2585', 'http://sbml.org', None),
            ),
            (
                ('param_1', 'param 1',
                 'float', 1.2, (0.12, 12.), ('KISAO', '00001', None, None, None)),
            )
        ))

    def test_AlgorithmParameter(self):
        param = AlgorithmParameter(id='param_1',
                                   name='param 1',
                                   type=Type.float,
                                   value=1.2,
                                   recommended_range=[0.12, 12.],
                                   kisao_term=OntologyTerm(ontology='KISAO', id='00001'))
        self.assertEqual(AlgorithmParameter.from_json(param.to_json()), param)
        self.assertEqual(AlgorithmParameter.sort_key(param), ('param_1', 'param 1',
                                                              'float', 1.2, (0.12, 12.), ('KISAO', '00001', None, None, None)))

    def test_ParameterChange(self):
        change = ParameterChange(parameter=AlgorithmParameter(id='param_1',
                                                              name='param 1',
                                                              type=Type.float,
                                                              value=1.2,
                                                              recommended_range=[0.12, 12.],
                                                              kisao_term=OntologyTerm(ontology='KISAO', id='00001')),
                                 value=2.1)
        self.assertEqual(ParameterChange.from_json(change.to_json(), AlgorithmParameter), change)
        self.assertEqual(ParameterChange.sort_key(change), (('param_1', 'param 1', 'float',
                                                             1.2, (0.12, 12.), ('KISAO', '00001', None, None, None)), 2.1))

    def test_SimulationResult(self):
        result = SimulationResult(simulation=TimecourseSimulation(id='sim'), variable=BiomodelVariable(id='var'))
        self.assertEqual(SimulationResult.from_json(result.to_json()), result)
        self.assertEqual(SimulationResult.sort_key(result), ('sim', 'var'))

""" Data model for visualizations

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-04-06
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from ..chart.data_model import Chart, ChartDataField
from ..data_model import Format, ResourceMetadata
from ..simulation.data_model import SimulationResult

__all__ = [
    'Visualization', 'VisualizationLayoutElement', 'VisualizationDataField',
]


class Visualization(object):
    """ Visualization of the results of one or more simulations

    Attributes:
        id (:obj:`str`): id
        format (:obj:`Format`): format
        columns (:obj:`int`): number of columns
        layout (:obj:`list` of :obj:`VisualizationLayoutElement`): element of the visualization
            (i.e. the cells in the grid of visualizations)
        metadata (:obj:`ResourceMetadata`): metadata
    """

    def __init__(self, id=None, format=None,
                 columns=None, layout=None, metadata=None):
        """
        Args:
            id (:obj:`str`, optional): id
            format (:obj:`Format`, optional): format
            columns (:obj:`int`, optional): number of columns
            layout (:obj:`list` of :obj:`VisualizationLayoutElement`, optional): element of the visualization
                (i.e. the cells in the grid of visualizations)
            metadata (:obj:`ResourceMetadata`, optional): metadata
        """
        self.id = id
        self.format = format
        self.columns = columns
        self.layout = layout or []
        self.metadata = metadata or ResourceMetadata()

    def __eq__(self, other):
        """ Determine if two simulations are semantically equal

        Args:
            other (:obj:`Simulation`): other simulation

        Returns:
            :obj:`bool`
        """
        return other.__class__ == self.__class__ \
            and self.id == other.id \
            and self.format == other.format \
            and self.columns == other.columns \
            and sorted(self.layout, key=VisualizationLayoutElement.sort_key) == \
            sorted(other.layout, key=VisualizationLayoutElement.sort_key) \
            and self.metadata == other.metadata

    def to_json(self):
        """ Export to JSON

        Returns:
            :obj:`dict`
        """
        return {
            'id': self.id,
            'format': self.format.to_json() if self.format else None,
            'columns': self.columns,
            'layout': [el.to_json() for el in self.layout],
            'metadata': self.metadata.to_json() if self.metadata else None,
        }

    @classmethod
    def from_json(cls, val):
        """ Create simulation from JSON

        Args:
            val (:obj:`dict`)

        Returns:
            :obj:`Simulation`
        """
        return cls(
            id=val.get('id', None),
            format=Format.from_json(val.get('format')) if val.get('format', None) else None,
            columns=val.get('columns', None),
            layout=[VisualizationLayoutElement.from_json(el) for el in val.get('layout', [])],
            metadata=ResourceMetadata.from_json(val.get('metadata')) if val.get('metadata', None) else None,
        )


class VisualizationLayoutElement(object):
    """ Element of a visualization (i.e. a cell in a grid of visualizations)

    Attributes:
        chart (:obj:`Chart`): chart type
        data (:obj:`list` of :obj:`VisualizationDataField`): data to paint chart type
    """

    def __init__(self, chart=None, data=None):
        """
        Args:
            chart (:obj:`Chart`, optional): chart type
            data (:obj:`list` of :obj:`VisualizationDataField`, optional): data to paint chart type
        """
        self.chart = chart
        self.data = data or []

    def __eq__(self, other):
        """ Determine if two elements are semantically equal

        Args:
            other (:obj:`VisualizationLayoutElement`): other element

        Returns:
            :obj:`bool`
        """
        return other.__class__ == self.__class__ \
            and self.chart == other.chart \
            and sorted(self.data, key=VisualizationDataField.sort_key) == sorted(other.data, key=VisualizationDataField.sort_key)

    def to_json(self):
        """ Export to JSON

        Returns:
            :obj:`dict`
        """
        return {
            'chartType': self.chart.to_json() if self.chart else None,
            'data': [d.to_json() for d in self.data],
        }

    @classmethod
    def from_json(cls, val):
        """ Create an element from JSON

        Args:
            val (:obj:`dict`)

        Returns:
            :obj:`VisualizationLayoutElement`
        """
        return cls(
            chart=Chart.from_json(val.get('chartType')) if val.get('chartType', None) else None,
            data=[VisualizationDataField.from_json(d) for d in val.get('data', [])],
        )

    @staticmethod
    def sort_key(el):
        """ Get a key to sort an element

        Args:
            el (:obj:`VisualizationLayoutElement`): element

        Returns:
            :obj:`tuple`
        """
        return (el.chart.id, tuple(sorted([VisualizationDataField.sort_key(d) for d in el.data])))


class VisualizationDataField(object):
    """
    Attributes:
        data_field (:obj:`ChartDataField`): data field
        simulation_results (:obj:`list` of :obj:`SimulationResult`): simulation results
    """

    def __init__(self, data_field=None, simulation_results=None):
        """
        Args:
            data_field (:obj:`ChartDataField`, optional): data field
            simulation_results (:obj:`list` of :obj:`SimulationResult`, optional): simulation results
        """
        self.data_field = data_field
        self.simulation_results = simulation_results or []

    def __eq__(self, other):
        """ Determine if two fields are semantically equal

        Args:
            other (:obj:`VisualizationDataField`): other field

        Returns:
            :obj:`bool`
        """
        return other.__class__ == self.__class__ \
            and self.data_field == other.data_field \
            and sorted(self.simulation_results, key=SimulationResult.sort_key) == \
            sorted(other.simulation_results, key=SimulationResult.sort_key)

    def to_json(self):
        """ Export to JSON

        Returns:
            :obj:`dict`
        """
        return {
            'dataField': self.data_field.to_json() if self.data_field else None,
            'simulationResults': [r.to_json() for r in self.simulation_results],
        }

    @classmethod
    def from_json(cls, val):
        """ Create field from JSON

        Args:
            val (:obj:`dict`)

        Returns:
            :obj:`VisualizationDataField`
        """
        return cls(
            data_field=ChartDataField.from_json(val.get('dataField')) if val.get('dataField', None) else None,
            simulation_results=[SimulationResult.from_json(r) for r in val.get('simulationResults', [])],
        )

    @staticmethod
    def sort_key(field):
        """ Get a key to sort a field

        Args:
            field (:obj:`VisualizationDataField`): field

        Returns:
            :obj:`tuple`
        """
        return (
            ChartDataField.sort_key(field.data_field),
            tuple(sorted([SimulationResult.sort_key(r) for r in field.simulation_results])),
        )

from __future__ import print_function
from __future__ import absolute_import
from __future__ import division
from pyura.helpers import check_safety

class ClusterResources:
    """Unicore Cluster Resources.

    This class describes the capabilities such as number of CPUs, Memory, etc.
    of a Unicore cluster instance.
    """

    _mem_conversion = {
        'K' : 1024,
        'M' : 1048576,
        'G' : 1073741824
    }

    @staticmethod
    def _convert_memory(string):
        number = string[:-1]
        unit = string[-1]
        rv = string
        if unit in _mem_conversion:
            rv = float(number) * _mem_conversion[unit]
        return rv

    @staticmethod
    def _extract_limits(string, func):
        return list(map(func, string.split('-')))

    def get_num_nodes(self):
        """Returns the maximum selectable number of nodes in the cluster.

        Returns:
            (int)	the maximum selectable number of nodes in the cluster.
        """
        return self.max_nodes

    def get_num_cpus_total(self):
        """Returns the maximum selectable number of CPUs in the cluster.

        Returns:
            (int)	the maximum selectable number of CPUs in the cluster.
        """
        return self.max_total_cpus

    def get_num_cpus_per_node(self):
        """Returns the maximum selectable number of CPUs per node.

        Returns:
            (int)	the maximum selectable number of CPUs per node.
        """
        return self.max_cpus_per_node

    def get_num_mem_per_node(self):
        """Returns the maximum selectable amount of Memory per node.

        Returns:
            (int)	the maximum selectable amount of Memory per node.
        """
        return self.max_mem_per_node

    def get_min_num_nodes(self):
        """Returns the minimum selectable number of nodes in the cluster.

        Returns:
            (int)	the minimum selectable number of nodes in the cluster.
        """
        return self.min_nodes

    def get_min_num_cpus(self):
        """Returns the minimum selectable number of CPUs in the cluster.

        Returns:
            (int)	the minimum selectable number of CPUs in the cluster.
        """
        return self.min_total_cpus

    def get_min_num_cpus_per_node(self):
        """Returns the minimum selectable number of CPUs per node.

        Returns:
            (int)	the minimum selectable number of CPUs per node.
        """
        return self.min_cpus_per_node

    def get_min_num_mem_per_node(self):
        """Returns the minimum selectable amount of memory per node.

        Returns:
            (int)	the minimum selectable amount of memory per node.
        """
        return self.min_mem_per_node

    def check_in_range_nodes(self, nodes):
        """Checks, if the given number of nodes is permitted.

        Returns:
            (boolean)   true, if the given number of nodes is permitted,
                        false otherwise.
        """
        return nodes >= self.min_nodes \
                and nodes <= self.max_nodes

    def check_in_range_cpus(self, cpus):
        """Checks, if the given number of CPUs is permitted.

        Returns:
            (boolean)   true, if the given number of CPUs is permitted,
                        false otherwise.
        """
        return cpus >= self.min_total_cpus \
                and cpus <= self.min_total_cpus

    def check_in_range_cpus_per_node(self, cpus):
        """Checks, if the given number of CPUs per node is permitted.

        Returns:
            (boolean)   true, if the given number of CPUs per node is permitted,
                        false otherwise.
        """
        return cpus >= self.min_cpus_per_node \
                and cpus <= self.max_cpus_per_node

    def check_in_range_mem_per_node(self, mem):
        """Checks, if the given amount of Memory per node is permitted.

        Returns:
            (boolean)   true, if the given number of Memory per node is
                        permitted, false otherwise.
        """
        m = ClusterResources._convert_memory(mem)
        return m >= self.min_mem_per_node \
                and m <= self.max_mem_per_node

    def get_queues(self):
        """Returns the available job queues as a list of strings.

        Returns:
            ([str])     list of available job queues.
        """
        return self.queues

    def update_from_json(self, json):
        """Updates the values hold by this instance of ClusterResources from
        the given JSON dict.

        Args:
            (dict)  JSON representation of a Unicore Cluster resource.
        """
        check_safety([(json, dict)])

        #TODO check argument validity

        self.min_nodes, self.max_nodes                  = ClusterResources\
                ._extract_limits(json['Nodes'], lambda x: int(float(x)))
        self.min_cpus_per_node, self.max_cpus_per_node  = ClusterResources\
                ._extract_limits(json['CPUsPerNode'], lambda x: int(float(x)))
        self.min_mem_per_node, self.max_mem_per_node    = ClusterResources\
                ._extract_limits(
                        json['MemoryPerNode'],
                        lambda x: int(float(x))
                        )
        self.min_total_cpus, self.max_total_cpus        = ClusterResources\
                ._extract_limits(json['TotalCPUs'], lambda x: int(float(x)))

        self.queues             = json['Queue']


    def __init__(self, json):
        """Initializes a new ClusterResources instance.

        Initial values will be parsed from the given JSON repersentation of a
        Unicore Cluster resource.

        Args:
            (dict)  JSON representation of a Unicore Cluster resource.
        """

        self.max_nodes              = 0
        self.max_cpus_per_node      = 0
        self.max_mem_per_node       = 0
        self.max_total_cpus         = 0
        self.min_nodes              = 0
        self.min_cpus_per_node      = 0
        self.min_mem_per_node       = 0
        self.min_total_cpus         = 0

        self.queues                 = []

        self.update_from_json(json)

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Optional, Tuple
from ...codes.elements import AncillaQubit



class Node(ABC):
    """Element in the node-tree.

    A subgraph :math:`\mathcal{V}\subseteq C` is a spanning-tree of a cluster :math:`C` if it is a connected acyclic subgraph that includes all vertices of :math:`C` and a minimum number of edges. We call the spanning-tree of a cluster its ancilla-tree. An acyclic connected spanning-forest is required for the Union-Find Decoder.

    A node-tree :math:`\mathcal{N}` is a partition of a ancilla-tree :math:`\mathcal{V}`, such that each element of the partition -- which we call a *node* :math:`n` -- represents a set of adjacent vertices that lie at the same distance -- the *node radius} :math:`r` -- from the *primer ancilla*, which initializes the node and lies at its center. The node-tree is a directed acyclic graph, and its edges :math:`\m{E}_i` have lengths equal to the distance between the primer vertices of neighboring nodes. 

    Paramters
    ---------
    primer
        Primer ancilla-qubit.

    Attributes
    ----------
    short : str
        Short name of the node.
    old_bound : list
        Current boundary edges.
    new_bound : list
        Next boundary edges.
    neighbors : list
        Neighboring nodes in the node-tree.
    root_list : list
        List of even subroots of merged node-trees.
    radius : int
        Node radius size.
    parity : {0,1}
        Node parity.
    delay : int
        Number of iterations to wait.
    waited : int
        Number of iterations waited.
    """

    short = "T"

    def __init__(self, primer: AncillaQubit):

        self.primer = primer
        primer.node = self

        self.old_bound = []
        self.new_bound = []
        self.neighbors = []
        self.root_list = []
        self.radius = 0
        self.parity = 0
        self.delay = 0
        self.waited = 0

    def __repr__(self):
        return f"{self.short}N{self.primer.loc}|{self.primer.z})"

    @property
    def _status(self):
        parity = "o" if self.parity else "e"
        return f"{self.radius}{parity}{self.waited}/{self.delay}"

    @property
    def _repr_status(self):
        return str(self) + self._status

    @abstractmethod
    def ns_parity(self):
        "Calculates and returns the parity of the current node."
        pass

    def ns_delay(self, parent: Optional[Tuple[Node, int]] = None, min_delay: Optional[int] = None) -> int:
        """Calculates the node delay.

        Head recursive function that calculates the delays of the current node and all its descendent nodes. 

        .. math:: n_d = m_d + \floor{n_r-m_r}- (-1)^{n_p}\abs{(n,m)}.

        The minimal delay ``min_delay`` in the tree is maintained as the actual delay is relative to the minimal delay value within the entire node-tree. 

        Parameters
        ----------
        parent
            The parent node and the distance to the parent node.
        min_delay
            Minimal delay value encountered during the current calculation.
        """
        self.root_list = []
        self.waited = 0

        if parent is not None:
            parent, edge = parent
            self.delay = parent.delay + (self.radius/2 - parent.radius/2) % 1 - edge * (-1) ** parent.parity
            if min_delay is None or (self.delay < min_delay):
                min_delay = self.delay

        for node, edge in self.neighbors:
            if node is not parent:
                min_delay = node.ns_delay((self, edge), min_delay)

        return min_delay


class Syndrome(Node):
    short = "S"
    def ns_parity(self, parent_node: Optional[Node] = None) -> int:
        """Calculates the node parity. 

        Tail recursive function that calculates the parities of the current node and all its descendent nodes.

        .. math:: s_p &= \hspace{.6cm}\big( \sum_{\mathclap{n \in \text{ children of } s}} (1+s_p) \big ) \bmod 2

        Parameters
        ----------
        parent_node
            Parent node in node-tree to indicate direction. 
        """
        self.parity = (
            sum(
                [1 - node.ns_parity(self) for node, _ in self.neighbors if node is not parent_node]
            )
            % 2
        )
        return self.parity

class Junction(Node):
    short = "J"

    def ns_parity(self, parent_node: Optional[Node] = None) -> int:
        """Calculates the node parity. 

        Tail recursive function that calculates the parities of the current node and all its children. 

        .. math:: j_p &= 1 - \big(\sum_{\mathclap{n \in \text{ children of } j}} (1+n_p) \big) \bmod 2.

        Parameters
        ----------
        parent_node
            Parent node in node-tree to indicate direction.
        """
        self.parity = 1 - (
            sum(
                [1 - node.ns_parity(self) for node, _ in self.neighbors if node is not parent_node]
            )
            % 2
        )
        return self.parity



class Boundary(Node):
    short = "B"

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.parity = 1

    def ns_parity(self, *args, **kwargs) -> int:
        # Inherited docsting
        return self.parity


class Filler(Node):
    short = "F"

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.parity = 1

    def ns_parity(self, *args, **kwargs) -> int:
        # Inherited docstring
        return self.parity

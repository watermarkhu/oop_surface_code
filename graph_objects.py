class iGraph(object):
    """
    The graph in which the vertices, edges and clusters exist. Has the following parameters

    C           dict of clusters with
                    Key:    cID number
                    Value:  Cluster object
    S           dict of stabilizers with
                    Key:    sID number
                    Value:  Stab object
    B           dict of open boundaries with
                    Key:    sID number
                    Value:  Boundary object
    Q           dict of qubits with
                    Key:    qID number
                    Value:  Qubit object with two Edge objects
    wind        dict keys from the possible directions of neighbors.

    """

    def __init__(self, size):
        self.size = size
        self.C = {}
        self.S = {}
        self.B = {}
        self.Q = {}
        self.wind = ["u", "d", "l", "r"]

    def __repr__(self):

        numC = 0
        for cluster in self.C.values():
            if cluster.parent == cluster:
                numC += 1
        return (
            "Graph object with "
            + str(numC)
            + " Clusters, "
            + str(len(self.S))
            + " Stabilizers,  "
            + str(len(self.Q))
            + " Qubits and "
            + str(len(self.B))
            + " Boundaries"
        )

    def add_cluster(self, cID):
        """Adds a cluster with cluster ID number cID"""
        self.C[cID] = iCluster(cID)
        return self.C[cID]

    def add_stab(self, sID):
        """Adds a stabilizer with stab ID number sID"""
        self.S[sID] = iStab(sID)
        return self.S[sID]

    def add_boundary(self, sID):
        """Adds a open bounday (stab like) with bounday ID number sID"""
        self.B[sID] = iBoundary(sID)
        return self.B[sID]

    def add_edge(self, qID, VL, VR, VU, VD):
        """Adds an edge with edge ID number qID with pointers to vertices. Also adds pointers to this edge on the vertices. """

        qubit = iQubit(qID)
        self.Q[qID] = qubit
        E1, E2 = (qubit.VXE, qubit.PZE) if qID[2] == 0 else (qubit.PZE, qubit.VXE)
        VL.neighbors["r"] = (VR, E1)
        VR.neighbors["l"] = (VL, E1)
        VU.neighbors["d"] = (VD, E2)
        VD.neighbors["u"] = (VU, E2)

        return qubit

    def reset(self):
        """
        Resets the graph by deleting all clusters and resetting the edges and vertices

        """
        self.C = {}
        for qubit in self.Q.values():
            qubit.reset()
        for stab in self.S.values():
            stab.reset()

    def grow_reset(self):
        self.C = {}
        for qubit in self.Q.values():
            qubit.grow_reset()
        for stab in self.S.values():
            stab.grow_reset()


    def measure_stab(self):
        """
        The measurement outcomes of the stabilizers, which are the vertices on the graph are saved to their corresponding vertex objects. We loop over all vertex objects and over their neighboring edge or qubit objects.
        """
        for stab in self.S.values():
            for dir in self.wind:
                if dir in stab.neighbors:
                    if stab.neighbors[dir][1].state:
                        stab.state = not stab.state


class iCluster(object):
    """
    Cluster obejct with parameters:
    cID         ID number of cluster
    size        size of this cluster based on the number contained vertices
    parity      parity of this cluster based on the number of contained anyons
    parent      the parent cluster of this cluster
    childs      the children clusters of this cluster
    full_edged  growth state of the cluster: 1 if False, 2 if True
    full_bound  boundary for growth step 1
    half_bound  boundary for growth step 2
    bucket      the appropiate bucket number of this cluster

    """

    def __init__(self, cID):
        # self.inf = {"cID": cID, "size": 0, "parity": 0}
        self.cID = cID
        self.size = 0
        self.parity = 0
        self.parent = self
        self.childs = [[], []]
        self.boundary = [[], []]
        self.bucket = 0
        self.support = 0

    def __repr__(self):
        return "C" + str(self.cID) + "(" + str(self.size) + ":" + str(self.parity) + ")"

    def add_stab(self, stab):
        """Adds a stabilizer to a cluster. Also update cluster value of this stabilizer."""
        self.size += 1
        if stab.state:
            self.parity += 1
        stab.cluster = self


class iStab(object):
    """
    Stab object with parameters:
    sID         location of stabilizer (ertype, y, x)
    neighbors   dict of the neighobrs (in the graph) of this stabilizer with
                    Key:    wind
                    Value   (Stab object, Edge object)
    state       boolean indicating anyon state of stabilizer
    cluster     Cluster object of which this stabilizer is apart of
    tree        boolean indicating whether this stabilizer has been traversed
    """

    def __init__(self, sID):
        # fixed paramters
        self.sID = sID
        self.neighbors = {}

        # iteration parameters
        self.state = False
        self.cluster = None
        self.tree = False

    def __repr__(self):
        type = "X" if self.sID[0] == 0 else "Z"
        return "v" + type + "(" + str(self.sID[1]) + "," + str(self.sID[2]) + ")"

    def reset(self):
        """
        Changes all iteration paramters to their initial value
        """
        self.state = False
        self.cluster = None
        self.tree = False

    def grow_reset(self):
        self.cluster = None
        self.tree = None


class iBoundary(iStab):
    def __repr__(self):
        type = "X" if self.sID[0] == 0 else "Z"
        return "b" + type + "(" + str(self.sID[1]) + "," + str(self.sID[2]) + ")"


class iQubit(object):

    def __init__(self, qID):
        self.qID = qID
        self.erasure = 0
        self.VXE = iEdge((0, qID[2]))
        self.PZE = iEdge((1, 1 - qID[2]))

    def __repr__(self):
        return "q({},{}:{})".format(*self.qID)

    def reset(self):
        self.erasure = 0
        self.VXE.reset()
        self.PZE.reset()

    def grow_reset(self):
        self.VXE.grow_reset()
        self.PZE.grow_reset()


class iEdge(object):
    """
    Edge object with parameters:
    type        type of this edge: 0 for X type connecting vertices, 1 for Z type connecting plaquettes
    vertices    tuple of the two conected vertices
    state       boolean indicating the state of the qubit
    cluster     Cluster object of which this edge is apart of
    peeled      boolean indicating whether this edge has peeled
    matching    boolean indicating whether this edge is apart of the matching
    """

    def __init__(self, type):
        # fixed parameters
        self.type = type

        # iteration parameters
        self.cluster = None
        self.state = 0
        self.support = 0
        self.peeled = 0
        self.matching = 0

    def __repr__(self):
        errortype = "X" if self.type[0] == 0 else "Z"
        orientation = "-" if self.type[1] == 0 else "|"
        return "e"+ errortype + orientation

    def reset(self):
        """
        Changes all iteration paramters to their initial value
        """
        self.cluster = None
        self.state = 0
        self.support = 0
        self.peeled = 0
        self.matching = 0

    def grow_reset(self):
        self.cluster = None
        self.support = 0
        self.peeled = 0


def init_toric_graph(size):

    graph = iGraph(size)
    graph.type = "toric"

    # Add vertices to graph
    for ertype in range(2):
        for y in range(size):
            for x in range(size):
                graph.add_stab((ertype, y, x))

    # Add edges to graph
    for y in range(size):
        for x in range(size):

            VL, VR = graph.S[(0, y, x)], graph.S[(0, y, (x + 1) % size)]
            VU, VD = graph.S[(1, (y - 1) % size, x)], graph.S[(1, y, x)]
            graph.add_edge((y, x, 0), VL, VR, VU, VD)

            VU, VD = graph.S[(0, y, x)], graph.S[(0, (y + 1) % size, x)]
            VL, VR = graph.S[(1, y, (x - 1) % size)], graph.S[(1, y, x)]
            graph.add_edge((y, x, 1), VL, VR, VU, VD)

    return graph


def init_planar_graph(size):

    graph = iGraph(size)
    graph.type = "planar"

    # Add vertices to graph
    for yx in range(size):
        for xy in range(size - 1):
            graph.add_stab((0, yx, xy + 1))
            graph.add_stab((1, xy, yx))

        graph.add_boundary((0, yx, 0))
        graph.add_boundary((0, yx, size))
        graph.add_boundary((1, -1, yx))
        graph.add_boundary((1, size - 1, yx))

    for y in range(size):
        for x in range(size):
            if x == 0:
                VL, VR = graph.B[(0, y, x)], graph.S[(0, y, x + 1)]
            elif x == size - 1:
                VL, VR = graph.S[(0, y, x)], graph.B[(0, y, x + 1)]
            else:
                VL, VR = graph.S[(0, y, x)], graph.S[(0, y, x + 1)]
            if y == 0:
                VU, VD = graph.B[(1, y - 1, x)], graph.S[(1, y, x)]
            elif y == size - 1:
                VU, VD = graph.S[(1, y - 1, x)], graph.B[(1, y, x)]
            else:
                VU, VD = graph.S[(1, y - 1, x)], graph.S[(1, y, x)]

            graph.add_edge((y, x, 0), VL, VR, VU, VD)

            if y != size - 1 and x != size - 1:
                VU, VD = graph.S[(0, y, x + 1)], graph.S[(0, y + 1, x + 1)]
                VL, VR = graph.S[(1, y, x)], graph.S[(1, y, x + 1)]
                graph.add_edge((y, x + 1, 1), VL, VR, VU, VD)

    return graph


def logical_error(graph):

    """
    Finds whether there are any logical errors on the lattice/graph. The logical error is returned as [Xvertical, Xhorizontal, Zvertical, Zhorizontal], where each item represents a homological Loop
    """
    if graph.type == "toric":

        logical_error = [0, 0, 0, 0]

        for i in range(graph.size):
            if graph.Q[(i, 0, 0)].VXE.state:
                logical_error[0] = not logical_error[0]
            if graph.Q[(0, i, 1)].VXE.state:
                logical_error[1] = not logical_error[1]
            if graph.Q[(i, 0, 1)].PZE.state:
                logical_error[2] = not logical_error[2]
            if graph.Q[(0, i, 0)].PZE.state:
                logical_error[3] = not logical_error[3]

        errorless = True if logical_error == [0, 0, 0, 0] else False
        return logical_error, errorless

    elif graph.type == "planar":

        logical_error = [False, False]

        for i in range(graph.size):
            if graph.Q[(i, 0, 0)].VXE.state:
                logical_error[0] = not logical_error[0]
            if graph.Q[(0, i, 0)].PZE.state:
                logical_error[1] = not logical_error[1]

        errorless = True if logical_error == [0, 0] else False
        return logical_error, errorless

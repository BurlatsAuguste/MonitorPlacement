package monitoring;

import java.util.BitSet;

import static monitoring.Utils.hashPair;

public class Route {
    final int index;
    final int src;
    final int dest;
    private BitSet nodes;

    public Route(int index, int src, int dest) {
        this.index = index;
        this.src = src;
        this.dest = dest;
    }

    public void setNodes(BitSet nodes) {
        this.nodes = nodes;
    }

    /**
     * @return the set of nodes crossed by the route (as a bitset)
     */
    public BitSet getNodes() {
        return this.nodes;
    }

    /**
     * @param nodeA index of node A
     * @param nodeB index of node B
     * @return true if the route allow to distinguish the two given nodes,
     *         false otherwise
     */
    public boolean distinguish(int nodeA, int nodeB) {
        return ((nodes.get(nodeA) && !nodes.get(nodeB)) ||
                (!nodes.get(nodeA) && nodes.get(nodeB)));
    }

    /**
     * compute the list of pair of nodes that the route makes distinguishables
     * @param nodeNbr the number of nodes
     * @return a bitset containing the pair of nodes
     */
    public BitSet getDiscrimSet(int nodeNbr) {
        BitSet discrimSet = new BitSet(nodeNbr*(nodeNbr-1)/2);
        for (int nodeA = 0; nodeA < nodeNbr; nodeA++) {
            if (nodes.get(nodeA)) {
                for (int nodeB = 0; nodeB < nodeA; nodeB++)
                    if (!nodes.get(nodeB))
                        discrimSet.set(hashPair(nodeA, nodeB, nodeNbr), true);
                for (int nodeB = nodeA +1 ; nodeB < nodeNbr; nodeB++)
                    if (!nodes.get(nodeB))
                        discrimSet.set(hashPair(nodeA, nodeB, nodeNbr), true);
            }
        }
        return discrimSet;
    }
}

package monitoring;

import java.util.ArrayList;
import java.util.BitSet;
import java.util.HashMap;
import java.util.HashSet;

import static monitoring.Utils.hashPair;

public class MonitorSelection extends Problem{

    private final HashSet<Integer> leafNodes;
    final private HashSet<Integer> monitors;
    protected int nbrReduction; //number of monitors discarded during optimisation of Solution
    protected int nbrCover; //number of added monitors during the cover loop
    protected int nbrOneId; //number of monitors after the 1id loop


    /**
     * Initialize a Monitor Selection Problem
     * @param routeFilename: path to the routes definition
     *      * @param oneId: true if the goal is 1-identifiability, false if it is cover
     */
    public MonitorSelection(String routeFilename, boolean oneId) {
        super(routeFilename, oneId);
        this.leafNodes = computeLeafNodes();
        this.monitors = new HashSet<>();
    }

    /**
     * @return the set of chosen monitors (requires to run solve() before)
     */
    public HashSet<Integer> getMonitors() {
        return this.monitors;
    }

    /**
     * Compute the set of leaf nodes in the network from the routes definitions
     * @return a hashset containing all the leaf nodes
     */
    public HashSet<Integer> computeLeafNodes() {
        HashSet<Integer> leafNodes = new HashSet<>(n);
        for (int i = 0; i < n; i++)
            leafNodes.add(i);
        BitSet routeNodes;
        for (Route route : routes) {
            routeNodes = route.getNodes();
            for (Integer node: leafNodes) {
                if (routeNodes.get(node) && node != route.src && node != route.dest) {
                    leafNodes.remove(node);
                    break;
                }
            }
        }
        return leafNodes;
    }

    /**
     * Compute the set of measurement paths from the set of monitors
     */
    public void computeMeasurementPaths() {
        for (Route route : routes)
            if (monitors.contains(route.src) && monitors.contains(route.dest))
                measurementPaths.add(route.index);
    }

    /**
     * Iteratively add monitors until each node in the network is covered by at least one
     * measurement path
     */
    public void cover() {

        //uncoveredNodes[i] is true if node i is uncovered, false otherwise
        BitSet uncoveredNodes = new BitSet(n);
        for(int i = 0; i < n; i++)
            uncoveredNodes.set(i);

        //all leaf nodes must be monitors
        monitors.addAll(leafNodes);

        //remove covered nodes
        if (monitors.size() > 2) {
            for (Route route: routes)
                if(monitors.contains(route.src) && monitors.contains(route.dest))
                    uncoveredNodes.andNot(route.getNodes());
        }

        int bestReduction = -1;
        int bestMonitor = -1;
        BitSet bestReductionSet = new BitSet(n);

        // reductionSets.get(i) contains the number of uncovered nodes that would be covered if
        // node i is chosen as a monitor
        HashMap<Integer, BitSet> reductionSets = new HashMap<>(n - monitors.size());
        for(int i = 0; i < n ; i++)
            if (!monitors.contains(i))
                reductionSets.put(i, new BitSet(n));


        while (!uncoveredNodes.isEmpty()) {
            for (BitSet set : reductionSets.values())
                set.clear();

            // Computes the reductionSets
            for (Route route : routes) {
                if (monitors.contains(route.src) && !monitors.contains(route.dest))
                    reductionSets.get(route.dest).or(route.getNodes());
                if (!monitors.contains(route.src) && monitors.contains(route.dest))
                    reductionSets.get(route.src).or(route.getNodes());
            }

            // Choose the monitor that would cover the most of uncovered nodes
            for (Integer node : reductionSets.keySet()) {
                reductionSets.get(node).and(uncoveredNodes);
                if (reductionSets.get(node).cardinality() > bestReduction) {
                    bestMonitor = node;
                    bestReduction = reductionSets.get(node).cardinality();
                    bestReductionSet.clear();
                    bestReductionSet.or(reductionSets.get(node));
                }
            }
            // update the set of uncovered nodes
            uncoveredNodes.andNot(bestReductionSet);
            //add the new monitor
            monitors.add(bestMonitor);
            reductionSets.remove(bestMonitor);
            bestReduction = -1;
        }
        this.nbrCover = monitors.size();

        if (!oneId)
            computeMeasurementPaths();
    }

    /**
     * Iteratively add monitors until each node in the network is 1-identifiable
     */
    public void oneId() {

        // Represents the set of indistiguishable pairs
        BitSet indistiguishablePairs = new BitSet(n*(n-1)/2);
        for (int i = 1; i < n; i++)
            for (int j = 0; j < i; j++)
                indistiguishablePairs.set(hashPair(j, i, n));

        // remove the pairs of nodes that are already distinguishables from the current set of monitors
        for (Route route: routes)
            if(monitors.contains(route.src) && monitors.contains(route.dest))
                indistiguishablePairs.andNot(route.getDiscrimSet(this.n));

        int bestImprovement = -1;
        int bestMonitor = -1;

        int[] improvement = new int[n];
        while (!indistiguishablePairs.isEmpty()) {
            for (int i = 0; i < n; i++)
                improvement[i] =0;

            // Compute for each non-monitor node the number of indistiguishable pairs of nodes
            // that would be distinguishables if it was added as a monitor
            for (int nodeA = 0; nodeA < n; nodeA++){
                for (int nodeB = 0; nodeB < nodeA; nodeB++) {
                    if (indistiguishablePairs.get(hashPair(nodeA, nodeB, n))) {
                        for (Route route: routes) {
                            if (monitors.contains(route.src) && !monitors.contains(route.dest) &&
                                    route.distinguish(nodeA, nodeB))
                                improvement[route.dest] += 1;
                            else if (!monitors.contains(route.src) && monitors.contains(route.dest) &&
                                    route.distinguish(nodeA, nodeB))
                                improvement[route.src] += 1;
                        }
                    }
                }
            }
            // choose the best monitor
            for (int i = 0; i < n; i++) {
                if (improvement[i] > bestImprovement) {
                    bestMonitor = i;
                    bestImprovement = improvement[i];
                }
            }

            // updates indistiguishablePairs
            for (Route route: routes)
                if ((monitors.contains(route.src) && route.dest == bestMonitor) ||
                        ((monitors.contains(route.dest) && route.src == bestMonitor)))
                    indistiguishablePairs.andNot(route.getDiscrimSet(n));
            // add the monitor
            monitors.add(bestMonitor);
            bestImprovement = -1;
        }
        this.nbrOneId = monitors.size() - this.nbrCover;
        computeMeasurementPaths();
    }

    /**
     * Test if the given monitor is redundant, i.e., if removing it would turn the network not entirely covered or 1-id
     * (depends on the problem's goal)
     * @param monitor the index of the monitor to test
     * @return true if the monitor is redundant, false otherwise
     */
    public boolean isMonitorRedundant(int monitor) {
        BitSet distinguishablesPairs = new BitSet(n*(n-1)/2);
        BitSet coveredNodes = new BitSet(n);

        for (Route route : routes) {
            if (route.src != monitor && route.dest != monitor &&
                    monitors.contains(route.src) && monitors.contains(route.dest)) {
                if (this.oneId)
                    distinguishablesPairs.or(route.getDiscrimSet(this.n));
                coveredNodes.or(route.getNodes());
            }
        }

        return (distinguishablesPairs.cardinality() == distinguishablesPairs.size() || !this.oneId) &&
                coveredNodes.cardinality() == coveredNodes.size();
    }

    /**
     * Iterates over the monitors and remove the redundant ones
     */
    public void optimizeSolution() {
        BitSet totalPairs = new BitSet(n*(n-1)/2);
        for (int i = 1; i < totalPairs.size(); i++)
            totalPairs.set(i, true);

        for (int m = 0; m < n; m++ )
            if (monitors.contains(m))
                if (isMonitorRedundant(m))
                    monitors.remove(m);

        this.nbrReduction = (this.nbrOneId + this.nbrCover) - monitors.size();
    }
}

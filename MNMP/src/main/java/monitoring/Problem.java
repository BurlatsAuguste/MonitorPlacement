package monitoring;

import java.io.BufferedReader;
import java.io.FileReader;
import java.io.IOException;
import java.util.*;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

import static monitoring.Utils.hashPair;

public abstract class Problem {

    protected int n; //number of nodes;
    protected ArrayList<Route> routes; //routes availables for the network
    protected boolean oneId; // true if the goal is 1-identifiability, false if it is cover
    final protected HashSet<Integer> measurementPaths; // indexes of the chosen measurement paths

    /**
     * Initialize the problem
     * @param routeFilename: path to the routes definition
     * @param oneId: true if the goal is 1-identifiability, false if it is cover
     */
    public Problem(String routeFilename, boolean oneId) {
        this.routes = new ArrayList<>();
        parseInstance(routeFilename);
        this.oneId = oneId;
        measurementPaths = new HashSet<>();
    }

    /**
     * Parse routes and number of nodes from the given instance file.
     * @param filename: the path to the file where routes are stored.
     */
    public void parseInstance(String filename) {
        int n = -1;
        try {
            BufferedReader reader = new BufferedReader(new FileReader(filename));

            Pattern findInt = Pattern.compile("\\d+");
            Matcher mInt;

            this.n = Integer.parseInt(reader.readLine().split(" ")[0]);

            String currentLine = reader.readLine();
            int startingNode;
            int endingNode;
            BitSet newRoute;
            while (currentLine != null) {
                mInt = findInt.matcher(currentLine);
                mInt.find();
                startingNode = Integer.parseInt(mInt.group());
                mInt.find();
                endingNode = Integer.parseInt(mInt.group());
                newRoute = new BitSet(this.n);
                int node;
                while (mInt.find()) {
                    node = Integer.parseInt(mInt.group());
                    newRoute.set(node);
                }
                this.routes.add(new Route(this.routes.size(), startingNode, endingNode));
                this.routes.get(this.routes.size() - 1).setNodes(newRoute);
                currentLine = reader.readLine();
            }


        } catch (IOException e) {
            System.out.println(e);
        }
    }

    public void cover() {
        System.out.println("Cover is not implemented for your type of problem");
    }

    public void oneId() {
        System.out.println("oneId is not implemented for your type of problem");
    }

    public void optimizeSolution() {
        System.out.println("optimization is not implemented for your type of problem");
    }

    /**
     * Solve the problem
     */
    public void solve() {
        this.cover();
        if (this.oneId)
            this.oneId();
        // this.optimizeSolution();
    }

    /**
     * @return an array list containing the chosen measurement path
     */
    public ArrayList<Route> getMeasurementPaths() {
        ArrayList<Route> measurementPathsDescription = new ArrayList<>();
        for (Integer path_index : measurementPaths) {
            measurementPathsDescription.add(routes.get(path_index));
        }
        return measurementPathsDescription;
    }

    /**
     * Verify that the solution makes the network entirely covered
     * necessitates to run solve() before
     * @return true if the network is covered, false otherwise
     */
    public boolean verifyCover() {
        BitSet coveredNodes = new BitSet(this.n);
        for (Integer i : this.measurementPaths) {
            coveredNodes.or(this.routes.get(i).getNodes());
        }
        return coveredNodes.cardinality() == this.n;
    }

    /**
     * Verify that the solution makes the network entirely 1-identifiable
     * necessitates to run solve() before
     * @return true if the network is 1-identifiable, false otherwise
     */
    public boolean verifyOneId() {
        BitSet totalPairs = new BitSet(n*(n-1)/2);
        for (int i = 1; i < n; i++)
            for (int j = 0; j < i; j++)
                totalPairs.set(hashPair(j, i, n));

        BitSet discrimPairs = new BitSet(n*(n-1)/2);
        for (Integer i: this.measurementPaths)
            discrimPairs.or(this.routes.get(i).getDiscrimSet(n));
        return discrimPairs.cardinality() == totalPairs.cardinality();
    }

    /**
     * @return a string containing a description of the measurement paths
     */
    public String solutionString() {
        StringBuilder solution = new StringBuilder();
        solution.append(n).append("\n");
        for (Integer a : measurementPaths) {
            solution.append(routes.get(a).src).append(" ").append(routes.get(a).dest)
                    .append(" | ");
            for (int i = 0; i < n; i++)
                if (routes.get(a).getNodes().get(i))
                    solution.append(i).append(" ");
            solution.append("\n");
        }
        return solution.toString();
    }
}

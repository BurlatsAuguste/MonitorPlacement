# Instances

## Directories 
In each directory :
- .routes files contain the list of routes in the networks
- .edges files contain the list of edges int the networks
- .rdc files contain the reduction for the monitor problem, i.e., the set of independant nodes and the biconnected components (without their articulation points)

**hop_couting_based/** contains instances where the set of routes has been computed as the set of shortest paths according 
to the number of hop

**IGP_weight_based/** contains instances where the set of routes has been computed as the set of shortest paths according 
to IGP weights (taken from repetita)

In each directory, there is a **graphs.csv** file containing various information about each instance.


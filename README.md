# Monitor Placement Problem

- **MNMP/** contains a Java implementation of the MNMP algorithm dedicated to the 1-identifiability.
- **exact_models/** contains python interface to run the problem on *Gurobi* solver and *cpmpy*.
- **instances/** contains various Monitor Placement instances
- **maxsat_solvers** contains the source code of the maxSAT solvers (only NuWLS-c for now)

Running a monitor placement instance on Gurobi, OR-Tools
--------------------------------------------------------

```
pip install ortools gurobipy # install the requirements
python exact_models/monitor_placement.py [-h] -i INPUT -s {gurobi,ortools,nuwls-c} -g {cover,1id} [-r] [-c] [--solution SOLUTION] [-t TIMELIMIT]
```
where ``<ARGS>`` are the argument passed to the model.

The required arguments are :
- ``-i <INSTANCE>`` the instance file, i.e. the file containing the set of routes
- ``-g <GOAL>`` the goal, ``cover`` solve the Monitor Cover Problem, ``1id`` solve the Monitor 1-identifiability Problem
- ``-s <SOLVER>`` the solver to use, either gurobi, ortools or nuwls-c (for the last see the dedicated section below)
The optional argument are :
- ``-r <REDUCTIONS>`` the file containing the problem reductions
- ``-c`` format the output of stats in csv format
- ``--solution <SOLUTION>`` the file to store the solution
- ``-t <TIMELIMIT>`` the timelimit in seconds (default is 1800s)

For example to solve Monitor Placement Problem for 1-identifiability with gurobi with problem reductions:

```python exact_models/monitor_placement.py -i instances/hop_counting_based/zoo/Aarnet.routes -g 1id -s gurobi -r instances/hop_counting_based/zoo/Aarnet.rdc```
Note: A Gurobi license is required to run the Gurobi model, more info [here](https://www.gurobi.com/solutions/licensing/)

Running a monitor placement instance on NuWLS-c
-----------------------------------------------
To run the maxSAT model you first need to compile the solver:
```
cd maxsat_solvers/NuWLS-c-2023/code/
make rs
```
Then you can run the model with 
```
python exact_models/monitor_placement.py -s nuwls-c -i INPUT -g {cover,1id} [-r] [-c] [--solution SOLUTION] [-t TIMELIMIT]
```

Running a monitor placement on MNMP
-----------------------------------

```
cd MNMP
mvn install
java -jar target/MonitoringProblem-1.0.jar <ARGS>
```
where ``<ARGS>`` are the argument passed to the model.

The required arguments are :
- ``--routes <ROUTES>`` the instance file, i.e. the file containing the set of routes
- ``--goal <GOAL>`` the goal (cover or 1id)
The optional arguments are :
- ``--print-csv`` format the output of stats in csv format
- ``--print-solution`` print the solution in the standard output
- ``--write-solution <FILE>`` write the solution in the given file

Sources
-------
NuWLS-c: 
>Chu, Y., Cai, S., Luo, C.: Nuwls-c-2023: Solver description. MaxSAT Evaluation
2023 p. 23 (2023)
>https://maxsat-evaluations.github.io/2023/

Gurobi:
>Gurobi Optimization, LLC: Gurobi Optimizer Reference Manual (2023), 
> https://www.gurobi.com

OR-Tools:
>OR-Tools CP-SAT v9.8. Laurent Perron et Frédéric Didier.
>  https://developers.google.com/optimization/cp/cp_solver

MNMP:
>Ma, L., He, T., Swami, A., Towsley, D., Leung, K.K.: On optimal monitor place-
ment for localizing node failures via network tomography. Performance Evalu-
ation 91, 16–37 (Sep 2015). 
> https://doi.org/10.1016/j.peva.2015.06.003

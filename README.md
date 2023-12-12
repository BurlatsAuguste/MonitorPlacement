# Monitor Placement Problem

- **MNMP/** contains a Java implementation of the MNMP algorithm dedicated to the 1-identifiability.
- **python_models/** contains python interface to run the problem on *Gurobi* solver and *cpmpy*.
- **minizinc/** contains minizinc models
- **instances/** contains various Monitor Placement instances

Running a monitor placement instance on Gurobi or OR-Tools
-----------------------------------------------

```
pip install ortools gurobipy # install the requirements
```

Note: A Gurobi license is required to run the Gurobi model, more info [here](https://www.gurobi.com/solutions/licensing/)


NuWLS-c : 
>Chu, Y., Cai, S., Luo, C.: Nuwls-c-2023: Solver description. MaxSAT Evaluation
2023 p. 23 (2023)
>https://maxsat-evaluations.github.io/2023/
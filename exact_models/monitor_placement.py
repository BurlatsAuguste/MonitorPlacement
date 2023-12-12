import argparse
import gc
from ortools.sat.python import cp_model
import gurobipy as gp
from gurobipy import GRB
from time import time
from itertools import combinations

from utils import parse_instance, read_reductions, compute_symptoms
from max_sat import write_clauses_monitor_problem, solve_maxsat
from pathlib import Path

DEFAULT_TIMEOUT = 1800
MEM_LIMIT = 20
RANDOM_SEED = 1863947


def min_set_ortools(n, number_route, symptoms, endpoints, timelimit, independant_nodes=None,
                    biconnected_components=None,
                    goal="cover"):
    """
    CP model to find the smallest set of monitors such as all nodes are 1-identifiable
    :param n: number of nodes
    :param number_route: number of routes
    :param symptoms: a list of set, symptoms[i] contains the indexes of the routes that cross node i
    :param endpoints: a list of tuples : endpoints[j] contains the starting and ending nodes of route j
    :param timelimit : the timelimit for the resolution of the model, in seconds
    :param independant_nodes: a set of integer, it contains the independent nodes
    :param biconnected_components: a 2D list, containing each biconnected components
                                that contains exactly one articulation point, this articulation point is not present in the lists
    :param goal: "cover" or "1id", indicates the goal
    :return: a list containing index of monitors in the graph, the total runtime (load + solving time) in seconds,
            the solving time in seconds, the status of the solver
    """
    start_timer = time()
    model = cp_model.CpModel()

    # Variables

    # x[i] = 1 if i is a monitor, 0 otherwise
    x = []
    for i in range(n):
        x.append(model.NewBoolVar(f"x[i]"))

    # y[j] = 1 if both ends of route j are monitors i.e.  x[orig(route(j))]=1 and x[dest[route(j)]=1
    y = []
    for i in range(number_route):
        y.append(model.NewBoolVar(f"y[i]"))

    # Constraints
    # y[j] = 1 iff x[start[j]] = 1 AND x[end[j]] = 1
    for index, (src, dest) in enumerate(endpoints):
        model.Add(x[src] + x[dest] == 2).OnlyEnforceIf(y[index])

    # each node needs to be covered by at least one route
    for p in symptoms:
        model.Add(sum([y[route] for route in p]) > 0)

    if goal == "1id":
        # each node needs to be distinguishable of every other nodes by at least one route
        for i in range(n):
            for j in range(i + 1, n):
                model.Add(sum([y[route] for route in symptoms[i].symmetric_difference(symptoms[j])]) > 0)

    # Redundant constraints and reductions

    # each independant node is assumed to be a monitor
    if independant_nodes is not None:
        for node in independant_nodes:
            model.Add(x[node] == 1)

        del independant_nodes
        gc.collect()

    # if a biconnected components contains only one articulation points
    # then at least one of its node should be a monitor
    if biconnected_components is not None:
        for component in biconnected_components:
            model.Add(sum([x[node] for node in component]) > 0)

        del biconnected_components
        gc.collect()

    # Objective function
    # We want to minimize the number of monitors
    monitors_nbr = sum(x)
    model.Minimize(monitors_nbr)

    solver = cp_model.CpSolver()
    solver.parameters.num_search_workers = 1
    solver.parameters.max_memory_in_mb = 1000 * MEM_LIMIT
    solver.parameters.max_time_in_seconds = timelimit

    status = solver.Solve(model)
    solving_time = solver.WallTime()
    end_timer = time()

    monitors = []
    # if a solution has been found, retrieves it
    if status == 4 or status == 2:
        for index, i in enumerate(x):
            if solver.Value(i):
                monitors.append(index)

    total_time = end_timer - start_timer

    solver_status = status

    return monitors, total_time, solving_time, solver_status


def min_set_gurobi(n, number_route, symptoms, endpoints, timelimit, independant_nodes=None, biconnected_components=None,
                   goal="cover"):
    """
    ILP model to find the smallest set of monitors such as each node is 1-identifiable
    :param n: number of nodes
    :param number_route: number of routes
    :param symptoms: a list of set, symptoms[i] contains the indexes of the routes that cross node i
    :param endpoints: a list of tuples : endpoints[j] contains the starting and ending nodes of route j
    :param timelimit : the timelimit for the resolution of the model, in seconds
    :param independant_nodes: a set of integer, it contains the independent nodes
    :param biconnected_components: a 2D list, containing each biconnected components
                                that contains exactly one articulation point, this articulation point is not present in the lists
    :param goal: "cover" or "1id", indicates the goal
    :return: a list containing index of monitors in the graph, the total runtime (load + solving time) in seconds,
            the solving time in seconds, the status of the solver
    """

    try:
        env = gp.Env(empty=True)
        env.setParam('OutputFlag', 0)
        env.start()
        start_timer = time()
        m = gp.Model("1id", env=env)
        m.setParam("NonConvex", 0)
        m.setParam('TimeLimit', timelimit)
        m.setParam('SoftMemLimit', MEM_LIMIT)
        m.setParam('Seed', RANDOM_SEED)
        #m.setParam('Presolve', 0)
        m.setParam(GRB.Param.Threads, 1)

        # Variables

        # x[i] = 1 if i is a monitor, 0 otherwise
        x = m.addVars([i for i in range(n)], name="X", vtype=GRB.BINARY)
        # y[j] = 1 if both ends of route j are monitors i.e.  x[orig(route(j))]=1 and x[dest[route(j)]=1
        y = m.addVars([j for j in range(number_route)], name="Y",
                      vtype=GRB.BINARY)

        # The objective is to minimize the number of monitors
        m.setObjective(gp.quicksum(x), GRB.MINIMIZE)

        # Constraints

        # y_ij <-> x_i · x_j
        m.addConstrs(x[src] - y[index] >= 0 for index, (src, dest) in enumerate(endpoints))
        m.addConstrs(x[dest] - y[index] >= 0 for index, (src, dest) in enumerate(endpoints))
        m.addConstrs(y[index] >= x[src] + x[dest] - 1 for index, (src, dest) in enumerate(endpoints))

        # each node needs to be covered by at least one route
        for i in range(n):
            m.addConstr(gp.quicksum([y[l] for l in symptoms[i]]) >= 1)

        if goal == "1id":
            # each node needs to be distinguishable of every other nodes by at least one route
            for i in range(n):
                for j in range(i + 1, n):
                    m.addConstr(gp.quicksum([y[l] for l in symptoms[i].symmetric_difference(symptoms[j])]) >= 1)

        # each independant node is assumed to be a monitor
        if independant_nodes is not None:
            for node in independant_nodes:
                m.addConstr(x[node] == 1.0)

            del independant_nodes
            gc.collect()

        # if a biconnected components contains only one articulation points
        # then at least one of its node should be a monitor
        if biconnected_components is not None:
            for component in biconnected_components:
                m.addConstr(gp.quicksum([x[i] for i in component]) >= 1)

            del biconnected_components
            gc.collect()

        m.optimize()
        end_timer = time()

        monitors = []
        # if a solution has been found, retrieves it
        if m.status == 2 or m.status == 9:
            for index, v in x.items():
                if v.getAttr("x"):
                    monitors.append(index)

        total_time = end_timer - start_timer
        solving_time = m.Runtime

        if m.status == 9:
            status = 'Timeout'
        elif m.status == 2:
            status = 'Optimal'
        elif m.status == 3:
            status = 'Infeasible'
        elif m.status == 17:
            status = 'MemoryError'
        else:
            status = 'Error'

        return monitors, total_time, solving_time, status

    except gp.GurobiError as e:
        print('Error code ' + str(e.errno) + ': ' + str(e))

    except AttributeError as e:
        print('Error code : ' + str(e))


def verify_1id(nbr_nodes, symptoms, path_set):
    """
    Test if the given set of measurement path allows each node to be 1-identifiable
    :param nbr_nodes: number of nodes in the graph
    :param symptoms: a list of set, symptoms[i] contains the indexes of the routes that cross node i
    :param path_set: a set containing the indexes of each measurement path
    :return: True if each node is 1-identifiable, False otherwise
    """
    for pair in combinations(range(nbr_nodes), 2):
        path_for_distinguish = symptoms[pair[0]].symmetric_difference(symptoms[pair[1]])
        if len(path_set.intersection(path_for_distinguish)) == 0:
            return False

    return True


def verify_cover(nbr_nodes, symptoms, path_set):
    """
        Test if the given set of measurement path allows each node to be 1-covered
        :param nbr_nodes: number of nodes in the graph
        :param symptoms: a list of set, symptoms[i] contains the indexes of the routes that cross node i
        :param path_set: a set containing the indexes of each measurement path
        :return: True if each node is covered, False otherwise
        """
    for node in range(nbr_nodes):
        if len(symptoms[node].intersection(path_set)) == 0:
            return False

    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input', help="instance file", required=True)
    parser.add_argument('-s', '--solver', help="choice of model",
                        choices=["gurobi", "ortools", "nuwls-c"], required=True)
    parser.add_argument('-g', '--goal', help="goal of model",
                        choices=["cover", "1id"], required=True)
    parser.add_argument('-r', '--reductions', help="use problem reductions", required=False,
                        action='store_true')
    parser.add_argument('-c', '--csv', help="set the output in csv format", required=False, action='store_true')
    parser.add_argument( '--solution', help="file to save the solution", required=False)
    parser.add_argument('-t', '--timelimit',
                        help='file to solve list of solutions objectives and time to found them', required=False)

    args = parser.parse_args()

    if args.timelimit:
        timeout = int(args.timelimit)
    else:
        timeout = DEFAULT_TIMEOUT

    n, routes_list = parse_instance(args.input)

    routes_nbr = len(routes_list)
    symptoms = compute_symptoms(n, routes_list)
    endpoints = [(route.start, route.end) for route in routes_list]

    del routes_list
    gc.collect()

    indy_nodes = None
    bicon_comp = None
    if args.reductions:
        # loads reductions
        reductions_file = args.input.replace('.routes', '.rdc')
        indy_nodes, bicon_comp = read_reductions(reductions_file)

    if args.solver == "gurobi":
        monitor_set, total_time, solving_time, status = min_set_gurobi(n, routes_nbr, symptoms,
                                                                                         endpoints,
                                                                                         timeout, indy_nodes,
                                                                                         bicon_comp, args.goal)
    elif args.solver == "nuwls-c":
        write_clauses_monitor_problem(n, symptoms, endpoints, args.goal, indy_nodes, bicon_comp,
                                       instance_name=Path(args.input).stem)
        monitor_set, total_time, solving_time, status = solve_maxsat(args.goal,
                                                                     instance_name=Path(args.input).stem,
                                                                     timelimit=timeout,
                                                                     nodes_nbr=n)
    else:  # ortools
        monitor_set, total_time, solving_time, status = min_set_ortools(n, routes_nbr, symptoms, endpoints,
                                                                        timeout, indy_nodes, bicon_comp, args.goal)

    # compute the set of measurement paths from the set of monitor
    path_set = set()
    for index, (src, dest) in enumerate(endpoints):
        if src in monitor_set and dest in monitor_set:
            path_set.add(index)

    # Verification of solutions
    is_covered = verify_cover(n, symptoms, path_set)
    is_one_id = verify_1id(n, symptoms, path_set)

    # Register the solution
    if args.solution:
        solution_string = ""
        for monitor in monitor_set:
            solution_string += f"{monitor} "
        file = open(args.solution, 'w')
        file.write(solution_string)
        file.close()

    if args.csv:
        print(
            f"{args.input};{args.model};{args.goal};{args.reductions};{len(monitor_set)};{solving_time};{total_time};"
            f"{status};{is_covered};{is_one_id}")
    else:
        print(f"Status : {status}\n"
              f"Number of monitors : {len(monitor_set)}\n"
              f"Solving Time (s) : {solving_time}\n"
              f"Total Time (s) : {total_time}\n"
              f"Coverage : {is_covered}\n"
              f"1id : {is_one_id}")

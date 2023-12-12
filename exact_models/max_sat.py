import os
import subprocess
import time
import gc

MEM_LIMIT = 20*1000


def write_clauses_monitor_problem(n, symptoms, endpoints, goal="cover",
                                independant_nodes=None, biconnected_components=None,
                                instance_name="clause"):
    """
    Write the model into wncf format in the given file
    :param n: number of nodes
    :param number_route: number of routes
    :param symptoms: a list of set, symptoms[i] contains the indexes of the routes that cross node i
    :param endpoints: a list of tuples : endpoints[j] contains the starting and ending nodes of route j
    :param goal: "cover" or "1id", indicates the goal
    :param independant_nodes: a set of integer, it contains the independent nodes
    :param biconnected_components: a 2D list, containing each biconnected components
                                that contains exactly one articulation point, this articulation point is not present in the lists
    :param instance_name: name of the file to store the clauses
    """

    # path to store temporary store the clauses
    if not os.path.isdir(os.path.join(os.path.dirname(__file__), f"tmp/clauses/")):
        os.makedirs(os.path.join(os.path.dirname(__file__), f"tmp/clauses/"))
    clause_path = os.path.join(os.path.dirname(__file__), f"tmp/clauses/{instance_name}_{goal}.tmp")
    clauses = []

    file = open(clause_path, 'w')

    # weights of monitors
    for i in range(n):
        clauses.append(["1", -(i + 1)])

    file.write(clauses_to_wcnf(clauses))
    file.flush()

    clauses = []

    # route is measurement path <-> its endpoints are both monitors
    for index, (src, dest) in enumerate(endpoints):
        clauses.append(["h", src+1, -(index+1+n)])
        clauses.append(["h", dest+1, -(index+1+n)])
        clauses.append(["h", -(src+1), -(dest+1), index+1+n])

    file.write(clauses_to_wcnf(clauses))
    file.flush()

    clauses = []

    # cover clauses
    for symptom in symptoms:
        clause = ["h"]
        for route in symptom:
            clause.append(route+1+n)

        clauses.append(clause)

    file.write(clauses_to_wcnf(clauses))
    file.flush()

    clauses = []

    # 1-identifiability clauses
    if goal == '1id':
        for node_a in range(n):
            for node_b in range(node_a + 1, n):
                clause = ["h"]
                for route in symptoms[node_a].symmetric_difference(symptoms[node_b]):
                    clause.append(route+1+n)

                clauses.append(clause)

            file.write(clauses_to_wcnf(clauses))
            file.flush()
            clauses = []

    # each independant node must be a monitor
    if independant_nodes is not None:
        for node in independant_nodes:
            clauses.append(["h", node+1])

        del independant_nodes
        gc.collect()

    # if a biconnected components contains only one articulation points
    # then at least one of its node should be a monitor
    if biconnected_components is not None:
        for component in biconnected_components:
            clause = ["h"]
            for node in component:
                clause.append(node+1)
            clauses.append(clause)

        del biconnected_components
        gc.collect()

    file.write(clauses_to_wcnf(clauses))
    file.close()


def clauses_to_wcnf(clauses):
    """
    Convert the clauses to the wncf format
    :param clauses: a 2D list containing each clause
    :return: a string containing the model in wcnf format
    """
    output_string = ""
    for clause in clauses:
        for elem in clause:
            output_string+=str(elem) + " "
        output_string += "0\n"
    return output_string


def get_solve_time(stat_file):
    """
    Retrieve the solving time from the statistics outputed by the solver
    :param stat_file: path to the file containing the statistics
    :return: a float containing the solving time (in seconds) if it is present,
            None otherwise
    """
    with open(stat_file, 'r') as file:
        lines = file.readlines()
        file.close()

    for line in lines:
        if line.strip().split("=")[0] == "WCTIME":
            return float(line.strip().split("=")[1])

    return None


def get_solution_paths(output):
    sol = None
    status = None
    for line in output.split('\n'):
        if len(line) > 0:
            if line[0:2] == "s ":
                status = line[2:].strip()
            if line[0:2] == "v ":
                sol = set([index for index, val in enumerate(line[1:].strip()) if val == "1"])

    return sol, status


def get_solution_monitors(output, n):
    """
    Retrieve the solution of the monitor placement problem
    :param output: a string containing the output of the solver
    :param n: the number of nodes
    :return: a set containing the chosen monitors, the solver status
    """
    sol = None
    status = None
    for line in output.split('\n'):
        if len(line) > 0:
            if line[0:2] == "s ":
                status = line[2:].strip()
            if line[0:2] == "v ":
                sol = set([index for index, val in enumerate(line[1:].strip()) if val == "1" and index < n])

    return sol, status


def solve_maxsat(goal = "cover",instance_name="clause", timelimit=1800, nodes_nbr=None):
    """
    Use NuWLS-c to solve the problem
    :param goal: "cover" or "1id"
    :param instance_name: name of the file containing the clauses
    :param timelimit: time limit (in seconds) for the solver
    :param nodes_nbr: the number of nodes
    :return: a list containing index of monitors in the graph, the total runtime (load + solving time) in seconds,
            the solving time in seconds, the status of the solver
    """

    # file where the stats will be written
    if not os.path.isdir(os.path.join(os.path.dirname(__file__), f"tmp/stats/")):
        os.makedirs(os.path.join(os.path.dirname(__file__), f"tmp/stats/"))
    if not os.path.isdir(os.path.join(os.path.dirname(__file__), f"tmp/watcher_info/")):
        os.makedirs(os.path.join(os.path.dirname(__file__), f"tmp/watcher_info/"))
    stats_path = os.path.join(os.path.dirname(__file__), f"tmp/stats/{instance_name}_{goal}.tmp")
    watch_path = os.path.join(os.path.dirname(__file__), f"tmp/watcher_info/{instance_name}_{goal}.tmp")
    # file where the clauses are written
    clause_path = os.path.join(os.path.dirname(__file__), f"tmp/clauses/{instance_name}_{goal}.tmp")
    # path to the solver
    executable_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "sat_solver/NuWLS-c-2023/bin")

    start_time = time.perf_counter()
    # solve the problem
    output = subprocess.getoutput(f"{os.path.join(executable_dir, 'run')} -W {timelimit} -d 3 -v {stats_path} "
                                     f"-w {watch_path} -M {MEM_LIMIT} "
                                     f"{os.path.join(executable_dir, 'NuWLS-c_static')} {clause_path}")
    total_time = time.perf_counter() - start_time

    solution, status = get_solution_monitors(output, nodes_nbr)
    solve_time = get_solve_time(stats_path)

    # remove the temp files
    os.remove(stats_path)
    os.remove(watch_path)
    os.remove(clause_path)

    return solution, total_time, solve_time, status
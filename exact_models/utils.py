from copy import deepcopy
from itertools import combinations
from time import perf_counter, time
import subprocess
import os


class Route:
    """
    class representing the routes
    """
    def __init__(self, start, end, nodes, index):
        """
        create a Route object
        :param start: integer corresponding to the starting node index
        :param end: integer corresponding to the destination node index
        :param nodes: set of integers containing the nodes crossed by the route
        :param index: index of the route
        """
        self.start = start
        self.end = end
        self.nodes = nodes
        self.index = index

    def __str__(self):
        return f"{self.index} | {self.start} {self.end} | {self.nodes}"

def compute_symptoms(n, routes_list):
    """
    Compute the symptom of each node from the set of availables routes
    :param n: the number of nodes
    :param routes_list: a list of Route objects containing the routes
    :return: a list of sets containing the symptom of each node
    """
    symptoms = [set() for i in range(n)]
    for route in routes_list:
        for node in route.nodes:
            symptoms[node].add(route.index)

    return symptoms


def routes_from_symptoms(m, symptoms, used_routes):
    """
    Retrieves the routes definition from the symptoms
    :param m: the number of routes
    :param symptoms: a list of sets containing the symptom of each node
    :param used_routes: the indexes of the wanted routes
    :return: a list of Route objects containing the wanted routes
    """
    routes = [Route(-1, -1, set(), i) for i in range(m)]  # TODO retrieve route's endpoints
    for node, symptom in enumerate(symptoms):
        for route in symptom:
            if route in used_routes:
                routes[route].nodes.add(node)

    return [route for index, route in enumerate(routes) if index in used_routes]


def read_reductions(reduction_file):
    """
    Parse reductions files for monitor problem
    :param reduction_file: path to the file containing the reductions definitions
    :return: a list containing the independant nodes, and a 2D list containing the biconnected components
            of the network that contains exactly one articulation point (the articulation point are removed from the
            components definitions)
    """
    with open(reduction_file, 'r') as file:
        lines = file.readlines()
    if lines[0].strip(): # si la ligne n'est pas vide
        independent_nodes = [int(node) for node in lines[0].strip().split(' ')]
    else:
        independent_nodes = []

    biconnected_components = []
    for line in lines[2:]:
        if line.strip():
            biconnected_components.append([int(node) for node in line.strip().split(' ')])

    return independent_nodes, biconnected_components


def parse_instance(filename):
    """
    parse instances
    :param filename: the path to the file containing the instance
    :return: a tuple (nodes_number, routes) where nodes_number is an integer representing the number of nodes
            and routes is a list of Route objects containing each available route in the network
    """
    with open(filename, 'r') as input_file:
        lines = input_file.readlines()

    nodes_number = int(lines[0].split(" ")[0])
    route_number = int(lines[0].split(" ")[1])

    routes = []
    for i in range(1, route_number+1):
        indexes, route_string = lines[i].split(' | ')
        index_a, index_b = indexes.split(" ")
        route = route_string.split(" ")
        routes.append(Route(int(index_a), int(index_b), set([int(node) for node in route]), i-1))

    return nodes_number, routes


def hash_pair(a, b, n):
    """
    Hash a pair of node to link it to its corresponding d_ij
    Depends on the total number of node
    TODO maybe simplify it
    :param a: index of first node
    :param b: index of second node
    :param n: total number of node
    :return: an integer representing the hash
    """
    if a >= n or b >= n : # or a < 0 or b < 0 or a == b:
        raise ValueError('value in pairs cannot be more or equal than n')
    if a < 0 or b < 0:
        raise ValueError('a and b cannot be negative')
    if a == b:
        raise ValueError('a and b cannot be equals')
    if a < b:
        return int((n-1)*(n-2)/2 - (n-a-1)*(n-a-2)/2) + b - 1
    else:
        return int((n-1)*(n-2)/2 - (n-b-1)*(n-b-2)/2 )+ a - 1

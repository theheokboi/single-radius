import json
import networkx as nx
import os

"""
File: as_relationships.py

Description:
This module is designed to process and analyze Autonomous System (AS) relationships.
It includes functionality to read AS relationship data from a file, parse the data into a usable format,
and write the data to JSON files. Additionally, it contains a function to create a NetworkX directed graph
from the AS relationship data.

Functions:
- read_as_relationships(file_path): Reads AS relationship data from a given file, parses it, and writes it to JSON files.
- create_networkx_graph(as_subset=None): Generates a NetworkX directed graph from the AS relationship JSON files.
"""

def read_as_relationships(file_path):
    """
    Reads AS relationship data from a given file, parses it, and writes it to JSON files.
    
    The function expects a file path to a text file containing AS relationship data. Each line in the file
    represents a relationship and should be in the format: <origin AS>|<connected AS>|<relationship type>,
    where <relationship type> is an integer (0 for peer-to-peer, -1 for provider-to-customer).
    
    The function processes each line, ignoring comments (lines starting with '#'), and constructs an adjacency list
    where each AS number is a key, and the value is a list of tuples representing connected AS numbers and the
    type of relationship.
    
    After processing the entire file, the function writes the adjacency list for each AS to a separate JSON file
    named <AS number>.json within the directory 'data/as-rel/json/'.
    
    Parameters:
    - file_path (str): The path to the file containing AS relationship data.
    
    Returns:
    None
    """
    adjacency_list = {}
    
    with open(file_path, 'r') as file:
        for line in file:
            if line.startswith('#'):
                continue
            origin_as, connected_as, relationship = line.strip().split('|')
            relationship = int(relationship)
            
            # Convert AS numbers from string to int for consistency
            origin_as = int(origin_as)
            connected_as = int(connected_as)
            
            # Add the origin AS if not present
            if origin_as not in adjacency_list:
                adjacency_list[origin_as] = []
            # Add the connected AS if not present
            if connected_as not in adjacency_list:
                adjacency_list[connected_as] = []
                
            # Handle P2P relationship
            if relationship == 0:
                adjacency_list[origin_as].append((connected_as, 'P2P'))
                # Also add the reverse relationship
                # adjacency_list[connected_as].append((origin_as, 'P2P'))
                
            # Handle P2C relationship
            elif relationship == -1:
                adjacency_list[origin_as].append((connected_as, 'P2C'))
                # Add the reverse relationship as C2P
                adjacency_list[connected_as].append((origin_as, 'C2P'))

    # Write each AS's adjacency list to a separate JSON file named after the AS number
    for as_number, connections in adjacency_list.items():
        with open(f'static/as-rel/json/{as_number}.json', 'w') as file:
            file.write(json.dumps({as_number: connections}))




def create_networkx_graph(as_subset=None):
    g = nx.DiGraph()
    directory = 'static/as-rel/json/'

    if as_subset is not None:
        files_to_process = [f"{as_number}.json" for as_number in as_subset if os.path.isfile(os.path.join(directory, f"{as_number}.json"))]
    else:
        files_to_process = os.listdir(directory)

    for filename in files_to_process:
        with open(os.path.join(directory, filename), 'r') as file:
            adjacency_list = json.load(file)
            for as_number, connections in adjacency_list.items():
                as_number = int(as_number)
                if as_number not in g:
                    g.add_node(as_number)
                for connected_as, relationship in connections:
                    connected_as = int(connected_as)
                    if connected_as not in g:
                        g.add_node(connected_as)
                    if relationship == 'C2P':
                        g.add_edge(connected_as, as_number, rel=-1, relationship='c2p')
                    elif relationship == 'P2C':
                        g.add_edge(as_number, connected_as, rel=-1, relationship='c2p')
                    else:  # P2P relationship
                        g.add_edge(as_number, connected_as, rel=0, relationship='p2p')
                        g.add_edge(connected_as, as_number, rel=0, relationship='p2p')

    return g
def get_neighbors(as_number):
    """
    Get the list of neighbors for a given AS number.

    :param as_number: The AS number for which to find neighbors.
    :return: A list of AS numbers that are neighbors of the given AS.
    """
    neighbors = []
    try:
        with open(f'static/as-rel/json/{as_number}.json', 'r') as file:
            adjacency_list = json.load(file)
            neighbors = [neighbor[0] for neighbor in adjacency_list[str(as_number)]]
    except FileNotFoundError:
        print(f"No data file found for AS number {as_number}.")
    except json.JSONDecodeError:
        print(f"Error decoding JSON from file for AS number {as_number}.")
    except KeyError:
        print(f"AS number {as_number} not found in the adjacency list.")
    
    return neighbors

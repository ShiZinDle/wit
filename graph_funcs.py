import os
from typing import Any, Dict, List, Optional

import matplotlib.pyplot as plt
import networkx as nx

import utilities


COLOR = '#1f78b4'
ARROW_PROPS = {'arrowstyle': 'simple', 'color': COLOR}
LABEL_DIF = 0.3
LABEL_DIF_2 = 0.03
DIVISOR = 50
BRANCH_DIVISOR = 10
DOUBLE_X = 0.015
DOUBLE_X_2 = 0.003
DOUBLE_Y = 0.1
DOUBLE_Y_2 = 0.01
ARROW_SIZE = 20
NODE_SIZE = 8000
EDGE_SIZE = 3


def get_adjacency(wit_dir: Optional[str] = None, branch_id: Optional[str] = None, all_commits: bool = False) -> Dict[str, List[str]]:
    """Return an 'adjacency list' dictionary of commit inheritance to draw a graph from."""
    if wit_dir is None:
        wit_dir = utilities.get_wit_dir()

    try:
        if branch_id:
            head_id = branch_id
        else:
            head_id = utilities.get_parent_id(wit_dir)['HEAD']
    except KeyError:
        head_id = 'None'

    adjacency: Dict[str, List[str]] = {}
    if head_id != 'None':
        adjacency[head_id] = utilities.get_parent_id(wit_dir, commit_id=head_id)['parent'].split(', ')
    update_adjacency(adjacency, wit_dir)

    if all_commits:
        for commit_id in os.listdir(os.path.join(wit_dir, 'images')):
            if '.txt' not in commit_id and commit_id not in adjacency:
                adjacency[commit_id] = utilities.get_parent_id(wit_dir, commit_id=commit_id)['parent'].split(', ')

    return adjacency


def update_adjacency(adjacency: Dict[str, List[str]], wit_dir: str) -> None:
    """Update adjacency list in `adjacency` based on its values."""
    length = len(adjacency)
    temp = list(adjacency.values())
    for commits in temp:
        for commit_id in commits:
            if commit_id not in adjacency and commit_id != 'None':
                adjacency[commit_id] = utilities.get_parent_id(wit_dir, commit_id=commit_id)['parent'].split(', ')
    if len(adjacency) != length:
        update_adjacency(adjacency, wit_dir)


def draw_graph(adjacency: Dict[str, List[str]], wit_dir: Optional[str] = None) -> None:
    """Draw a graph based on 'adjacency list' provided in `adjacency`."""
    if wit_dir is None:
        try:
            wit_dir = utilities.get_wit_dir()
        except FileNotFoundError as err:
            print(err)
            return None

    G = nx.DiGraph()
    for key, value in adjacency.items():
        for v in value:
            if v != 'None':
                G.add_edge(key, v)
    pos = add_annotation(G, wit_dir)
    nx.draw(G, pos=pos, arrowstyle='-|>', arrowsize=ARROW_SIZE, node_size=NODE_SIZE,
            width=EDGE_SIZE, edge_color=COLOR, with_labels=True, font_color='w',
            labels={node: f'{node[:8]}\n{node[8:16]}\n{node[16:24]}\n{node[24:32]}\n{node[32:40]}' for node in G.nodes})

    plt.show()


def add_annotation(G: Any, wit_dir: str) -> Any:
    """Add labels with branch names to nodes in `G`"""
    pos = nx.circular_layout(G)
    pos_len = len(pos)
    if pos_len == 1:
        label_dif = LABEL_DIF_2
        double_x = DOUBLE_X_2
        double_y = DOUBLE_Y_2
    else:
        label_dif = LABEL_DIF + pos_len / DIVISOR
        double_x = DOUBLE_X + pos_len / DIVISOR
        double_y = DOUBLE_Y
    branches = utilities.get_parent_id(wit_dir)
    all_ids: List[str] = []
    for branch_name in branches:
        branch_id = branches[branch_name]
        if branch_id in pos:
            branch_pos = pos[branch_id]
            branch_label = [branch_pos[0] - label_dif, branch_pos[1] - label_dif / BRANCH_DIVISOR]
            if branch_id in all_ids:
                count = all_ids.count(branch_id)
                branch_label = [branch_label[0] - double_x, branch_label[1] + double_y * count]
            plt.annotate(branch_name, xy=branch_pos, xytext=branch_label, arrowprops=ARROW_PROPS)
            all_ids.append(branch_id)
    return pos
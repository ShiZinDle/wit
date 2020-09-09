import os
from typing import Optional

import graph_funcs
import status_funcs
import utilities


def get_shared_parent(branch_name: str, wit_dir: Optional[str] = None) -> str:
    """Return commit id of the shared parent of `branch_name` and the current image."""
    if wit_dir is None:
        wit_dir = utilities.get_wit_dir()

    branch_id = utilities.get_branch_id(branch_name, wit_dir)
    branch_adjacency = graph_funcs.get_adjacency(wit_dir, branch_id=branch_id)
    for parent in graph_funcs.get_adjacency(wit_dir):
        if parent in branch_adjacency or parent in branch_adjacency.values():
            return parent
    return ''


def update_staging_area(parent_id: str, branch_name: str, wit_dir_parent: Optional[str] = None) -> None:
    """Replace all files in staging area that were changed between the images `parent_id` and `branch_name`."""
    if wit_dir_parent is None:
        wit_dir_parent = utilities.get_wit_dir_parent()
    wit_dir = os.path.join(wit_dir_parent, '.wit')
    branch_id = utilities.get_branch_id(branch_name, wit_dir)
    parent_path, branch_path = (os.path.join(wit_dir, 'images', commit_id) for commit_id in (parent_id, branch_id))
    changed = status_funcs.get_changed_files(parent_path, branch_path)
    nonexistent = status_funcs.get_nonexistent_files(parent_path, branch_path)
    for file_list in (changed, nonexistent):
        for file in file_list:
            new_path = utilities.get_new_path(file, wit_dir_parent, additions=['images', branch_id])
            utilities.copy_files(mode='a', path=new_path)
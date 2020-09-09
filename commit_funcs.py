import os
import random
import time
from typing import Optional

import utilities


HEXADECIMAL_CARS = ('1', '2', '3', '4',
                    '5', '6', '7', '8',
                    '9', '0', 'a', 'b',
                    'c', 'd', 'e', 'f')


def generate_commit_id() -> str:
    """Return a randomly generated id."""
    return ''.join(random.choice(HEXADECIMAL_CARS) for _ in range(40))


def create_references_file(commit_id: str, wit_dir: Optional[str] = None) -> None:
    """Create a reference file in `wit_dir`."""
    if wit_dir is None:
        try:
            wit_dir = utilities.get_wit_dir()
        except FileNotFoundError as err:
            print(err)
            return
    reference_path = os.path.join(wit_dir, 'references.txt')
    if not os.path.exists(reference_path):
        with open(reference_path, 'x') as references:
            references.write(f'HEAD={commit_id}\nmaster={commit_id}')


def create_metadata_file(commit_id: str, *message: str, merged_branch_id: Optional[str] = None, wit_dir: Optional[str] = None) -> None:
    """Create a metadata file for the current image."""
    if wit_dir is None:
        try:
            wit_dir = utilities.get_wit_dir()
        except FileNotFoundError as err:
            print(err)
            return
    images_dir = os.path.join(wit_dir, 'images')
    metadata_path = os.path.join(images_dir, f'{commit_id}.txt')
    try:
        parent = utilities.get_parent_id(wit_dir)['HEAD']
        if merged_branch_id:
            parent += f', {merged_branch_id}'
    except KeyError:
        parent = 'None'
    cur_time = time.strftime('%a %b %d %H:%M:%S %Y %z', time.gmtime())
    printable = f'parent={parent}\ndate={cur_time}'
    if message:
        to_print = ' '.join(message)
        printable += f'\nmessage={to_print}'
    with open(metadata_path, 'x') as metadata:
        metadata.write(printable)


def update_references(commit_id: str, wit_dir: Optional[str] = None, checkout: bool = False) -> None:
    """Update the reference file in `wit_dir`."""
    if wit_dir is None:
        try:
            wit_dir = utilities.get_wit_dir()
        except FileNotFoundError as err:
            print(err)
            return
    reference_path = os.path.join(wit_dir, 'references.txt')
    active_branch = utilities.get_active_branch(wit_dir)
    active_branch_id = utilities.get_parent_id(wit_dir)[active_branch]
    if not checkout and active_branch_id == utilities.get_parent_id(wit_dir)['HEAD']:
        active_branch_id = commit_id
    with open(reference_path, 'r') as file_handler:
        reference = file_handler.readlines()
    text = ''
    for line in reference:
        branch_name, branch_id = line.rstrip().split('=')
        if branch_name == 'HEAD':
            branch_id = commit_id
        elif branch_name == active_branch:
            branch_id = active_branch_id
        text += f'{branch_name}={branch_id}\n'
    with open(reference_path, 'w') as file_handler:
        file_handler.write(text.rstrip())
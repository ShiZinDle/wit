import os
import shutil
import sys
from typing import List, Optional, Tuple

import commit_funcs
import graph_funcs
import merge_funcs
import status_funcs
import utilities


FUNCS = ('help', 'init', 'add', 'commit',
         'status', 'checkout', 'rm',
         'graph', 'branch', 'merge')


def init(path: str) -> None:
    """Create a `.wit` directory for storing the program's images."""
    wit_dir = os.path.join(path, '.wit')
    images_dir = os.path.join(wit_dir, 'images')
    staging_area_dir = os.path.join(wit_dir, 'staging_area')
    try:
        for directory in [wit_dir, images_dir, staging_area_dir]:
            os.mkdir(directory)
    except FileExistsError as err:
        print('An error has occurred:\n{}'.format(err))
    else:
        utilities.update_activated('master')
        print('Wit initialized.')


def add(path: str) -> None:
    """Add a file or directory to be backed to staging area."""
    utilities.copy_files(mode='a', path=path)
    print(f'\'{path}\' added to staging area.')


def commit(*message: str, merged_branch_id: Optional[str] = None) -> None:
    """Create an image of files in staging area."""
    try:
        wit_dir = utilities.get_wit_dir()
    except FileNotFoundError as err:
        print(err)
        return

    staging_area = os.path.join(wit_dir, 'staging_area')
    changes, _, _, removed = status(no_print=True)
    if not changes and not removed:
        print('No changes since last commit')
        return
    commit_id = commit_funcs.generate_commit_id()
    utilities.copy_files(mode='c', path=staging_area, commit_id=commit_id)
    commit_funcs.create_metadata_file(commit_id, *message, merged_branch_id=merged_branch_id, wit_dir=wit_dir)
    try:
        commit_funcs.update_references(commit_id, wit_dir)
    except KeyError:
        commit_funcs.create_references_file(commit_id, wit_dir)
    print(f'Image {commit_id} created.')


def status(no_print: bool = False) -> Tuple[List[str], List[str], List[str], List[str]]:
    """Print commitment status of files."""
    parent_dir = utilities.get_wit_dir_parent()
    wit_dir = os.path.join(parent_dir, '.wit')
    staging_area = os.path.join(wit_dir, 'staging_area')
    try:
        head_id = utilities.get_parent_id(wit_dir)['HEAD']
    except KeyError:
        head_id = ''
        changes = [os.path.join(parent_dir, path) for path in os.listdir(staging_area)]
        removed = []
    else:
        last_image = os.path.join(wit_dir, 'images', head_id)
        changes = list(status_funcs.get_nonexistent_files(staging_area, last_image))
        changes.extend(list(status_funcs.get_changed_files(staging_area, last_image)))
        removed = list(status_funcs.get_nonexistent_files(last_image, parent_dir))
    unstaged = list(status_funcs.get_changed_files(parent_dir, staging_area))
    untracked = list(status_funcs.get_nonexistent_files(parent_dir, staging_area))

    if not no_print:
        printable = ''
        if head_id:
            printable += f'Current commit id: {head_id}'
            active_branch = utilities.get_active_branch(wit_dir)
            if active_branch:
                printable += f'\nActive branch: {active_branch}'
        else:
            printable += 'No images currently exist.'
        printable += (f'\n\nChanges to be committed:\n{changes}'
                      f'\n\nUnstaged changes:\n{unstaged}'
                      f'\n\nUntracked files:\n{untracked}'
                      f'\n\nRemoved files:\n{removed}')
        print(printable)

    return changes, unstaged, untracked, removed


def checkout(commit_id: str) -> None:
    """Rollback to a previous image."""
    try:
        wit_dir_parent = utilities.get_wit_dir_parent()
    except FileNotFoundError as err:
        print(err)
        return

    wit_dir = os.path.join(wit_dir_parent, '.wit')
    branches = utilities.get_parent_id(wit_dir)
    if commit_id not in branches and commit_id not in os.listdir(os.path.join(wit_dir, 'images')):
        print('Invalid commit id. Unable to perform checkout.')
        return

    changes, unstaged, _, _ = status(no_print=True)
    if changes or unstaged:
        print('Unable to perform checkout. There are changes not yet committed.')
        return

    if commit_id in branches:
        branch_name = commit_id
        commit_id = branches[commit_id]
    elif commit_id in branches.values():
        for key, value in branches.items():
            if value == commit_id:
                branch_name = key
    else:
        branch_name = ''
    utilities.update_activated(branch_name, wit_dir)
    for file in status_funcs.get_all_files(os.path.join(wit_dir, 'images', commit_id)):
        og_path = utilities.get_original_name(file)
        staging_area = utilities.get_new_path(og_path, wit_dir_parent, additions=['staging_area'])

        for path in (og_path, staging_area):
            if os.path.exists(path):
                try:
                    os.remove(path)
                except PermissionError:
                    shutil.rmtree(path)
            try:
                shutil.copy2(file, path)
            except PermissionError:
                shutil.copytree(file, path)

    commit_funcs.update_references(commit_id, wit_dir, checkout=True)
    print(f'Reverted to {commit_id}')


def rm(original_path: str) -> None:
    """Remove file from directory and staging_area."""
    try:
        path = utilities.get_abs_path(original_path)
        parent_dir = utilities.get_wit_dir_parent()
    except FileNotFoundError as err:
        print(err)
        return

    if '.wit' in path:
        print('Invalid path. Use path to original file.')

    new_path = utilities.get_new_path(path, parent_dir, additions=['staging_area'])
    for file in (path, new_path):
        if os.path.exists(file):
            try:
                os.remove(file)
            except PermissionError:
                shutil.rmtree(file)
    print(f'\'{original_path}\' removed.')


def graph(all_commits: bool = False) -> None:
    """Draw a graph of commit inheritance."""
    try:
        wit_dir = utilities.get_wit_dir()
    except FileNotFoundError as err:
        print(err)
        return

    graph_funcs.draw_graph(graph_funcs.get_adjacency(wit_dir, all_commits=all_commits), wit_dir)


def branch(branch_name: str) -> None:
    """Label the current commit id as `branch_name`, and define it as the acctivated branch."""
    try:
        wit_dir = utilities.get_wit_dir()
    except FileNotFoundError as err:
        print(err)
        return

    branches = utilities.get_parent_id(wit_dir)
    head_id = branches['HEAD']
    reference = os.path.join(wit_dir, 'references.txt')
    if branch_name not in branches:
        with open(reference, 'a') as file_handler:
            file_handler.write(f'\n{branch_name}={head_id}')
        print(f'Branch \'{branch_name}\' created.')
    else:
        print(f'A branch named \'{branch_name}\' already exists.')


def merge(branch_name: str) -> None:
    """Merge changes made in `branch_name` and in the current image into a new image."""
    try:
        wit_dir_parent = utilities.get_wit_dir_parent()
    except FileNotFoundError as err:
        print(err)
        return
    wit_dir = os.path.join(wit_dir_parent, '.wit')
    try:
        merge_funcs.update_staging_area(
            merge_funcs.get_shared_parent(branch_name, wit_dir),
            branch_name, wit_dir_parent)
    except ValueError as err:
        print(err)
    message = f'Merged branch: {branch_name}'
    branch_id = utilities.get_branch_id(branch_name)
    commit(message, merged_branch_id=branch_id)
    active_branch = utilities.get_active_branch(wit_dir)
    print(f'Branches \'{active_branch}\' & \'{branch_name}\' merged.')


if len(sys.argv) == 1 or sys.argv[1] == 'help' or sys.argv[1] not in FUNCS or len(sys.argv) > 3 and sys.argv[1] != 'commit':
    utilities.print_help()
else:
    if sys.argv[1] == 'init':
        if len(sys.argv) == 3:
            utilities.print_help()
        else:
            init(os.getcwd())
    elif sys.argv[1] == 'add':
        try:
            add(sys.argv[2])
        except IndexError:
            print('Usage: python <wit.py> add <path>')
    elif sys.argv[1] == 'commit':
        try:
            commit(*sys.argv[2:])
        except IndexError:
            commit()
        except FileNotFoundError as err:
            print(err)
    elif sys.argv[1] == 'status':
        if len(sys.argv) == 3:
            utilities.print_help()
        else:
            try:
                status()
            except FileNotFoundError as err:
                print(err)
    elif sys.argv[1] == 'checkout':
        try:
            checkout(sys.argv[2])
        except IndexError:
            print('Usage: python <wit.py> checkout <commit_id | branch_name>')
    elif sys.argv[1] == 'rm':
        try:
            rm(sys.argv[2])
        except IndexError:
            print('Usage: python <wit.py> rm <original_path>')
    elif sys.argv[1] == 'graph':
        try:
            if sys.argv[2] == '--all':
                graph(all_commits=True)
            else:
                print('Usage: python <wit.py> graph [--all]')
        except IndexError:
            graph()
    elif sys.argv[1] == 'branch':
        try:
            branch(sys.argv[2])
        except IndexError:
            print('Usage: python <wit.py> branch <name>')
    elif sys.argv[1] == 'merge':
        try:
            merge(sys.argv[2])
        except IndexError:
            print('Usage: python <wit.py> merge <branch_name>')
import os
import shutil
from typing import Dict, List, Optional


def print_help() -> None:
    """Print usage help for wit.py."""
    message = ('\nUsage: python <wit.py> <function name> [parameters]\n'
               '\nFunctions: Description, [Parameters]'
               '\n----------------------------------'
               '\ninit: Create a directory for image storage'
               '\nadd: Add a file or directory to be backed to staging area, <path>'
               '\ncommit: Create an image of files in staging area, [message]'
               '\nstatus: Print commitment status of files'
               '\ncheckout: Rollback to a previous image, <commit_id | branch_name>'
               '\nrm: Remove file from directory and staging_area, <original_path>'
               '\ngraph: Draw a graph of commit inheritance, [--all]'
               '\nbranch: Label the current commit id as <name> and define it as the acctivated branch, <name>'
               '\nmerge: Merge changes made in `branch_name` and in the current image into a new image, <branch_name>')
    print(message)


def get_abs_path(path: str) -> str:
    """Return absolute path to `path`."""
    if not os.path.exists(path):
        raise FileNotFoundError('`{}` doesn\'t exist.'.format(path))
    return os.path.abspath(path)


def get_wit_dir_parent(path: Optional[str] = None) -> str:
    """"Return path to first parent directory containing a '.wit' directory."""
    if path is None:
        path = os.getcwd()
    wit_dir_parent = None
    temp = path
    while not wit_dir_parent and not os.path.ismount(temp):
        if os.path.isdir(temp) and '.wit' in os.listdir(temp):
            return temp
        temp = os.path.dirname(temp)

    if wit_dir_parent is None:
        raise FileNotFoundError("'.wit' directory not found in `{}` or any of it's parent directories.".format((path)))


def get_wit_dir(path: Optional[str] = None) -> str:
    """Return path to '.wit' directory."""
    if path is None:
        path = os.getcwd()
    return os.path.join(get_wit_dir_parent(path), '.wit')


def get_new_path(abs_path: str,
                 wit_dit_parent: str,
                 additions: Optional[List[str]] = None,
                 commit: bool = False) -> str:
    """Return new path to be used for copying file located in `abs_path`."""
    temp_path = wit_dit_parent.split(os.sep)
    length = len(temp_path)
    temp_path.append('.wit')
    if additions:
        temp_path.extend(additions)
    if not commit:
        temp_path.extend(abs_path.split(os.sep)[length:])
    new_path = (os.sep).join(temp_path)
    return new_path


def copy_files(mode: str, path: str, commit_id: Optional[str] = None) -> None:
    """Copy files from `path` to the necessary location based on `mode`:
    if 'a', copy to staging_area
    if 'c', copy to images\`commit_id`"""

    if mode == 'a':
        try:
            path = get_abs_path(path)
            wit_dir_parent = get_wit_dir_parent(path)
        except FileNotFoundError as err:
            print(err)
            return
        new_path = get_new_path(path, wit_dir_parent, additions=['staging_area'])
        if os.path.exists(new_path):
            try:
                os.remove(new_path)
            except PermissionError:
                shutil.rmtree(new_path)

    elif mode == 'c':
        if commit_id is None:
            print('Missing argument: `commit_id`')
            return
        try:
            wit_dir_parent = get_wit_dir_parent()
        except FileNotFoundError as err:
            print(err)
            return
        new_path = get_new_path(path, wit_dir_parent, additions=['images', commit_id], commit=True)

    else:
        print('Invalid mode.\nAccepted modes:\n\'a\': add\n\'c\': commit')
        return

    try:
        shutil.copytree(path, new_path)
    except NotADirectoryError:
        try:
            shutil.copy2(path, new_path)
        except FileNotFoundError:
            split_path = new_path.split(os.sep)
            for index, _ in enumerate(split_path):
                if index > 0:
                    temp_path = os.sep.join(split_path[:index])
                    if not os.path.exists(temp_path):
                        os.mkdir(temp_path)
            shutil.copy2(path, new_path)


def get_parent_id(wit_dir: Optional[str] = None, commit_id: Optional[str] = None) -> Dict[str, str]:
    """return parent id from reference or metadata file."""
    if wit_dir is None:
            wit_dir = get_wit_dir()
    if commit_id:
        path = os.path.join(wit_dir, 'images', f'{commit_id}.txt')
    else:
        path = os.path.join(wit_dir, 'references.txt')
    try:
        with open(path, 'r') as file_handler:
            return {line.split('=')[0]: line.split('=')[1].rstrip() for line in file_handler.readlines()}
    except FileNotFoundError:
        return {}


def get_original_name(path: str) -> str:
    """Return path to backed file in the 'real' directory."""
    temp = path.split(os.sep)
    for word in ('.wit', 'staging_area', 'images'):
        if word in temp:
            if word == 'images' and len(temp) > temp.index(word) + 1:
                temp.pop(temp.index(word) + 1)
            temp.remove(word)
    return os.sep.join(temp)


def update_activated(branch_name: str, wit_dir: Optional[str] = None) -> None:
    """Rewrite the contents of '.wit\\activated.txt' to `branch_name`."""
    if wit_dir is None:
        wit_dir = get_wit_dir()
    activated = os.path.join(wit_dir, 'activated.txt')
    with open(activated, 'w') as file_handler:
        file_handler.write(branch_name)


def get_branch_id(branch_name: str, wit_dir: Optional[str] = None) -> str:
    """Return commit id attached to `branch_name`."""
    if wit_dir is None:
        wit_dir = get_wit_dir()
    if branch_name in os.listdir(os.path.join(wit_dir, 'images')):
        return branch_name
    reference = os.path.join(wit_dir, 'references.txt')
    with open(reference, 'r') as file_handler:
        branches = {line.split('=')[0]: line.rstrip().split('=')[1]
                    for line in file_handler.readlines()}
    if branch_name in branches:
        return branches[branch_name]
    else:
        raise ValueError('Branch not found.')


def get_active_branch(wit_dir: Optional[str]) -> str:
    """Return the name of the active branch."""
    if wit_dir is None:
        wit_dir = get_wit_dir()
    activated = os.path.join(wit_dir, 'activated.txt')
    with open(activated, 'r') as file_handler:
        return file_handler.read()
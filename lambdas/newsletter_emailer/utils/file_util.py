import os


def recursive_glob(root_folder, file_ends_with='', output_relative_path=True):
    """
    Return recursive list of files in root_folder
    :param root_folder: Folder to look into
    :param file_ends_with: Filter files by ending string, use '' to match all files
    :param output_relative_path: Output relative path if True, else output absolute path
    :return: List of file paths
    """
    result = [os.path.join(dirpath, f)
              for dirpath, dirnames, files in os.walk(root_folder)
              for f in files if f.endswith(file_ends_with)]
    if output_relative_path:
        result = [os.path.relpath(x, root_folder) for x in result]
    return result


if __name__ == '__main__':
    folder = os.path.abspath(os.path.join('..'))
    print(folder)
    result = recursive_glob(folder, '', True)
    print(result)

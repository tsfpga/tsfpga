

def file_contains_string(file, string):
    with open(file) as file_handle:
        return string in file_handle.read()


def file_equals(file, string):
    with open(file) as file_handle:
        return file_handle.read() == string

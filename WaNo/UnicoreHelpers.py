
def extract_storage_path(path):
    storage = None
    querypath = ''
    splitted = [p for p in path.split('/') if not p is None and p != ""]

    if len(splitted) >= 1:
        storage   = splitted[0]
    if len(splitted) >= 2:
        querypath = '/'.join(splitted[1:]) if len(splitted) > 1 else ''

    return (storage, querypath)




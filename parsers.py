import pathlib


def parse_tags_file(file_path):
    tags = []
    current_tags_group = {
        'group_name': None,
        'tags': [],
    }
    with pathlib.Path(file_path).open() as f:
        for line in f.readlines():
            if line[-1] == ':':
                if current_tags_group['group_name']:
                    tags.append((current_tags_group['group_name'], tuple(current_tags_group['tags'])))
                    current_tags_group['group_name'] = None
                    current_tags_group['tags'] = []
                else:
                    current_tags_group['group_name'] = line[:-1]
            elif line[0] == '-':
                if not current_tags_group['group_name']:
                    raise Exception(f'Item {repr(line)} defined beyond a group.')
                current_tags_group['tags'].append(line[2:])
            elif line:
                tags.append(line)
        if current_tags_group['group_name']:
            tags.append((current_tags_group['group_name'], tuple(current_tags_group['tags'])))


def parse_tags_files(dir_path):
    tags_files = [
        file for file in pathlib.Path(dir_path).iterdir() if file.suffix == '.txt' and file.name.startswith('tags')
    ]
    return [parse_tags_file(file) for file in tags_files]

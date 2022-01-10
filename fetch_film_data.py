#!/usr/bin/env python3

from dataclasses import dataclass
import json
import os.path
import pathlib
import random
import requests


def get_env_data_as_dict(path: str) -> dict:
    with open(path, 'r') as f:
       return dict(tuple(line.replace('\n', '').split('=')) for line
                in f.readlines() if not line.startswith('#'))

env_vars = get_env_data_as_dict('.env.local')
BASE_URL = env_vars['KITSU_API_TARGET']
# JWT = None  # Set at runtime

# HEADERS = {'headers': {'Authorization': f"Bearer {JWT}"}}

COLORS_PALETTE = [
    [0.8197601437568665, 0.7117544412612915, 0.5497459173202515, 1.0],
    [0.6462640762329102, 0.5692625641822815, 0.8191020488739014, 1.0],
    [0.5096713304519653, 0.7521656155586243, 0.5136501789093018, 1.0],
    [0.8272907137870789, 0.5883985161781311, 0.6541866064071655, 1.0],
    [0.5273313522338867, 0.6598359346389770, 0.7609495520591736, 1.0],
    [0.7392144799232483, 0.7697654366493225, 0.5531221032142639, 1.0],
    [0.7357943654060364, 0.5509396195411682, 0.7686146497726440, 1.0],
    [0.5617250204086304, 0.7625861167907715, 0.6736904978752136, 1.0],
    [0.8007439970970154, 0.6388462185859680, 0.5802854895591736, 1.0],
    [0.6019799709320068, 0.6073563694953918, 0.8074616789817810, 1.0],
    [0.5944148898124695, 0.7527848482131958, 0.5205842256546020, 1.0],
    [0.8126696348190308, 0.5513396859169006, 0.7106873989105225, 1.0],
    [0.5918391346931458, 0.7710464000701904, 0.7906153798103333, 1.0],
    [0.7648254632949829, 0.7191355228424072, 0.5285170674324036, 1.0],
    [0.6757139563560486, 0.5736276507377625, 0.7719092965126038, 1.0],
    [0.5477100014686584, 0.7845347523689270, 0.6005358695983887, 1.0],
    [0.7501454353332520, 0.5404607057571411, 0.5548738241195679, 1.0],
    [0.5506091117858887, 0.6321061849594116, 0.7766551971435547, 1.0],
    [0.7142684459686279, 0.7983494400978088, 0.5565086007118225, 1.0],
    [0.6019799709320068, 0.5404607057571411, 0.7686146497726440, 1.0],
]


@dataclass
class KitsuClient:
    """Client to query the Kitsu API."""
    base_url: str
    jwt: float

    @property
    def headers(self):
        return {'Authorization': f"Bearer {self.jwt}"}

    def get(self, path, params=None):
        return requests.get(f"{self.base_url}{path}", params=params, headers=self.headers, allow_redirects=True)

    # def get_asset_type(self):
    #     return self.get('/data/asset-types')


def hex_to_rgba(hex):
    color = hex.lstrip('#')
    color = [int(color[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    color.append(1.0)
    return color


def generate_preview_file_path(file_id: str) -> pathlib.Path:
    """Generate a normalized file path.
    This forces .png extension, which for now is ok since all image
    file use that extension, and we do not need to deal with videos.

    For example:
    - 0a32d425-6723-4f2b-baf7-2a6d457fa669
    becomes:
    - 0a3/2d4/0a32d425-6723-4f2b-baf7-2a6d457fa669.png
    """
    folder_one = file_id[:3]
    folder_two = file_id[3:6]
    filename = f'{file_id}.png'
    return pathlib.Path('public') / 'static-previews' / folder_one / folder_two / filename


def fetch_jwt() -> str:
    payload = {
        'email': env_vars['KITSU_USER_EMAIL'],
        'password': env_vars['KITSU_USER_PASSWORD']
    }
    r_jwt = requests.post(f"{BASE_URL}/auth/login", data=payload)
    r_jwt = r_jwt.json()
    if 'error' in r_jwt:
        print(r_jwt['message'])
        exit()
    return r_jwt['access_token']


kitsu_client = KitsuClient(base_url=env_vars['KITSU_API_TARGET'], jwt=fetch_jwt())


def fetch_user_context():
    r_context = kitsu_client.get('/data/user/context')
    return r_context.json()


def fetch_and_save_image(src_url, dst: pathlib.Path, force=False):
    if not dst.is_file() or force:
        dst.parent.mkdir(parents=True, exist_ok=True)
        r_file = kitsu_client.get(src_url)
        dst.write_bytes(r_file.content)


def fetch_project(project):
    return kitsu_client.get(f"/data/projects/{project['id']}").json()


def fetch_asset_types():
    # r_asset_types = requests.get(f"{BASE_URL}/data/asset-types", **HEADERS)
    r_asset_types = kitsu_client.get('/data/asset-types')
    asset_types = []
    for asset_type in r_asset_types.json():
        asset_types.append({'name': asset_type['name'], 'id': asset_type['id']})
    return asset_types


def fetch_assets_and_previews(project, force=False):
    r_assets = kitsu_client.get('/data/assets/with-tasks', params={'project_id': project['id']})
    parsed_assets = []

    for asset in r_assets.json():
        if asset['canceled']:
            continue
        print(f"Processing asset {asset['name']}")
        asset_preview_name = 'placeholder-asset' if not asset['preview_file_id'] else asset['preview_file_id']
        dst = f"public/static-previews/placeholder-asset.png" if not asset['preview_file_id'] else ''
        # If thumbnail is not found locally, download it
        if asset['preview_file_id']:
            # dst = generate_preview_file_path(asset['preview_file_id'])
            src_url = f"pictures/thumbnails/preview-files/{asset['preview_file_id']}.png"
            dst = pathlib.Path(f"public/static-previews/{src_url}")
            fetch_and_save_image(src_url, dst)
        # Format data as expected by edit breakdown
        tasks = []
        for task in asset['tasks']:
            tasks.append({
                'task_status_id': task['task_status_id'],
                'task_type_id': task['task_type_id'],
                'assignees': task['assignees'],
            })
        parsed_assets.append({
            'id': asset['id'],
            'asset_type_id': asset['asset_type_id'],
            'name': asset['name'],
            'thumbnailUrl': str(dst).replace('public/', ''),
            'tasks': tasks,
        })

    return parsed_assets


def fetch_people():
    r_people = kitsu_client.get('/data/persons')

    people = []
    for person in r_people.json():
        dst = 'public/static-previews/pictures/thumbnails/persons/placeholder.png'
        if person['has_avatar']:
            src = f"pictures/thumbnails/persons/{person['id']}.png"
            dst = f"public/static-previews/{src}"
            fetch_and_save_image(src, pathlib.Path(dst))

        people.append({
            'name': person['full_name'],
            'id': person['id'],
            'profilePicture': dst,
            'color': random.choice(COLORS_PALETTE),
        })

    return people


def fetch_sequences(project):
    r_sequences = kitsu_client.get('/data/sequences', params={'project_id': project['id']})
    sequences = []
    for sequence in r_sequences.json():
        sequences.append({'name': sequence['name'], 'id': sequence['id']})
    return sequences


def fetch_casting(project):
    for sequence in fetch_sequences(project):
        r_casting = kitsu_client.get(f"/data/projects/{project['id']}/sequences/{sequence['id']}/casting")
        casting_per_shot = r_casting.json()
        if not casting_per_shot:
            continue
        dst = pathlib.Path(f"public/static-projects/{project['id']}/sequences/{sequence['id']}/casting.json")
        dst.parent.mkdir(parents=True, exist_ok=True)
        with open(dst, 'w') as outfile:
            json.dump(casting_per_shot, outfile, indent=2)


def fetch_task_types():
    r_task_types = requests.get(f"{BASE_URL}/data/task-types", **HEADERS)
    r_task_types = r_task_types.json()
    if 'error' in r_task_types:
        print(r_task_types['message'])
        exit()
    task_types = []
    for task in r_task_types:
        color = hex_to_rgba(task['color'])

        task_types.append({
            'name': task['name'],
            'color': color,
            'id': task['id'],
            'for_shots': task['for_shots']
        })
    return task_types


def fetch_task_statuses():
    r_task_statuses = requests.get(f"{BASE_URL}/data/task-status", **HEADERS)
    task_statuses = []
    for task in r_task_statuses.json():
        color = hex_to_rgba(task['color'])

        task_statuses.append({'name': task['name'], 'color': color, 'id': task['id']})
    return task_statuses


def fetch_shots_and_previews(project, force=False):
    # r_shots = requests.get(f"{BASE_URL}/data/shots/with-tasks", **HEADERS)
    r_shots = kitsu_client.get('/data/shots/with-tasks', params={'project_id': project['id']})
    parsed_shots = []

    for shot in r_shots.json():
        print(f"Processing shot {shot['name']}")
        if 'frame_in' not in shot['data']:
            print("Skipping shot with no frame_in data")
            continue
        if shot['preview_file_id']:
            # dst = f"public/preview-files/{shot['preview_file_id']}.png"
            # dst = generate_preview_file_path(shot['preview_file_id'])
            src_url = f"/pictures/thumbnails/preview-files/{shot['preview_file_id']}.png"
            dst = pathlib.Path(f"public/static-previews/{src_url}")
            fetch_and_save_image(src_url, dst)
        else:
            dst = None
        # Format data as expected by edit breakdown
        tasks = []
        for task in shot['tasks']:
            tasks.append({
                'task_status_id': task['task_status_id'],
                'task_type_id': task['task_type_id'],
                'assignees': task['assignees'],
            })
        parsed_shots.append({
            'id': shot['id'],
            'name': shot['name'],
            'thumbnailUrl': None if not dst else str(dst).replace('public/', ''),
            'startFrame': shot['data']['frame_in'],
            'durationSeconds': (shot['data']['frame_out'] - shot['data']['frame_in']) / int(project['fps']),
            'tasks': tasks,
            'sequence_id': shot['sequence_id'],
        })

    return parsed_shots


def build_edit_data():
    edit_data = {
        'sourceBase': 'http://eb.local:8080/',
        'sourceName': 'sf-edit-v106.mp4',
        'sourceType': 'video/mp4',
        'totalFrames': 14043,
        'frameOffset': 100,
        'fps': 24,
        # 'taskTypes': fetch_task_types(),
        # 'taskStatuses': fetch_task_statuses(),
        # 'shots': fetch_shots_and_previews(),
        # 'sequences': fetch_sequences(),
        # 'users': fetch_people(),
        # 'assetTypes': fetch_asset_types(),
        # 'assets': fetch_assets_and_previews(),
        # 'casting': fetch_casting(),
    }
    with open('public/edit.json', 'w') as outfile:
        json.dump(edit_data, outfile, indent=2)


# build_edit_data()


def save_user_context():
    """Save globally available settings.

    In particular, we are interested in these:

    - asset_types
    - persons
    - projects
    - task_types
    - task_status
    """
    with open('public/context.json', 'w') as outfile:
        user_context = fetch_user_context()
        for project in user_context['projects']:
            # Fetch project thumbnail
            src_url = f"/pictures/thumbnails/projects/{project['id']}.png"
            dst = pathlib.Path(f"public/static-previews/{src_url}")
            fetch_and_save_image(src_url, dst)
            project['thumbnailUrl'] = str(dst).replace('public/', '')
        json.dump(user_context, outfile, indent=2)
        print('Saved user context')


def dump_data(project, name, data):
    with open(f"public/static-projects/{project['id']}/{name}.json", 'w') as outfile:
        json.dump(data, outfile, indent=2)
    print(f"Saved {name} data for project {project['id']}")


def save_project_data(project):
    project_data = {
        'project': fetch_project(project),
        'shots': fetch_shots_and_previews(project),
        'sequences': fetch_sequences(project),
        'assets': fetch_assets_and_previews(project),
    }

    for k, v in project_data.items():
        dump_data(project, k, v)

    # with open(f"public/static-projects/{project['id']}/project.json", 'w') as outfile:
    #     json.dump(project_data, outfile, indent=2)
    # print(f"Saved project data for {project['id']}")


save_user_context()
fetch_people()

for p in fetch_user_context()['projects']:
    save_project_data(p)
    fetch_casting(p)


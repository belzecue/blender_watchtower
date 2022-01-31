#!/usr/bin/env python3

from dataclasses import dataclass
import json
import pathlib
import requests


def get_env_data_as_dict(path: str) -> dict:
    with open(path, 'r') as f:
        return dict(tuple(line.replace('\n', '').split('=')) for line
            in f.readlines() if not line.startswith('#'))


env_vars = get_env_data_as_dict('.env.local')
BASE_URL = env_vars['KITSU_DATA_SOURCE_URL']


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
        'email': env_vars['KITSU_DATA_SOURCE_USER_EMAIL'],
        'password': env_vars['KITSU_DATA_SOURCE_USER_PASSWORD']
    }
    r_jwt = requests.post(f"{BASE_URL}/auth/login", data=payload)
    r_jwt = r_jwt.json()
    if 'error' in r_jwt:
        print(r_jwt['message'])
        exit()
    return r_jwt['access_token']


kitsu_client = KitsuClient(base_url=BASE_URL, jwt=fetch_jwt())


def fetch_user_context():
    return kitsu_client.get('/data/user/context').json()


def fetch_and_save_image(src_url, dst: pathlib.Path, force=False):
    if not dst.is_file() or force:
        dst.parent.mkdir(parents=True, exist_ok=True)
        r_file = kitsu_client.get(src_url)
        dst.write_bytes(r_file.content)


def fetch_project(project):
    return kitsu_client.get(f"/data/projects/{project['id']}").json()


def fetch_asset_types():
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
        dst = f"public/static-previews/placeholder-asset.png" if not asset['preview_file_id'] else ''
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


def fetch_and_save_people_avatars():
    r_people = kitsu_client.get('/data/persons')

    people = []
    for person in r_people.json():
        dst = 'public/static-previews/placeholder-user.png'
        if person['has_avatar']:
            src = f"pictures/thumbnails/persons/{person['id']}.png"
            dst = f"public/static-previews/{src}"
            fetch_and_save_image(src, pathlib.Path(dst))

        people.append({
            'name': person['full_name'],
            'id': person['id'],
            'profilePicture': dst,
        })

    return people


def fetch_sequences(project):
    r_sequences = kitsu_client.get('/data/sequences', params={'project_id': project['id']})
    sequences = []
    for sequence in r_sequences.json():
        sequences.append({'name': sequence['name'], 'id': sequence['id']})
    return sequences


def fetch_and_save_casting(project):
    for sequence in fetch_sequences(project):
        r_casting = kitsu_client.get(f"/data/projects/{project['id']}/sequences/{sequence['id']}/casting")
        casting_per_shot = r_casting.json()
        if not casting_per_shot:
            continue
        dst = pathlib.Path(f"public/static-projects/{project['id']}/sequences/{sequence['id']}/casting.json")
        dst.parent.mkdir(parents=True, exist_ok=True)
        with open(dst, 'w') as outfile:
            json.dump(casting_per_shot, outfile, indent=2)


def fetch_shots_and_previews(project, force=False):
    r_shots = kitsu_client.get('/data/shots/with-tasks', params={'project_id': project['id']})
    parsed_shots = []

    for shot in r_shots.json():
        print(f"Processing shot {shot['name']}")
        if 'frame_in' not in shot['data']:
            print("Skipping shot with no frame_in data")
            continue
        if shot['preview_file_id']:
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
            'durationSeconds': (int(shot['data']['frame_out']) - int(shot['data']['frame_in'])) / int(project['fps']),
            'tasks': tasks,
            'sequence_id': shot['sequence_id'],
            'data': shot['data'],
        })

    return parsed_shots


def generate_edit_data(project, shots):
    edit_data = {
        'sourceName': f"/static-projects/{project['id']}/edit.mp4",
        'sourceType': 'video/mp4',
        'totalFrames': int(shots[-1]['data']['frame_out']) - int(shots[0]['data']['frame_in']),
        'frameOffset': int(shots[0]['data']['frame_in']),
    }
    dst = pathlib.Path(f"public/static-projects/{project['id']}/edit.json")
    dst.parent.mkdir(parents=True, exist_ok=True)
    with open(str(dst), 'w') as outfile:
        json.dump(edit_data, outfile, indent=2)


def fetch_and_save_context():
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
        # Fetch project thumbnails
        for project in user_context['projects']:
            src_url = f"/pictures/thumbnails/projects/{project['id']}.png"
            dst = pathlib.Path(f"public/static-previews/{src_url}")
            fetch_and_save_image(src_url, dst)
            project['thumbnailUrl'] = str(dst).replace('public/', '')
        # Remove private details from users
        processed_users = []
        for user in user_context['persons']:
            processed_users.append({
                'full_name': user['full_name'],
                'has_avatar': user['has_avatar'],
                'id': user['id']
            })
        user_context['persons'] = processed_users
        json.dump(user_context, outfile, indent=2)
        print('Saved user context')


def dump_data(project, name, data):
    dst = pathlib.Path(f"public/static-projects/{project['id']}/{name}.json")
    dst.parent.mkdir(parents=True, exist_ok=True)
    with open(dst, 'w') as outfile:
        json.dump(data, outfile, indent=2)
    print(f"Saved {name} data for project {project['id']}")


def save_project_data(project):
    shots = fetch_shots_and_previews(project)
    shots.sort(key=lambda x: x['startFrame'])
    project_data = {
        'project': fetch_project(project),
        'shots': shots,
        'sequences': fetch_sequences(project),
        'assets': fetch_assets_and_previews(project),
    }

    for k, v in project_data.items():
        dump_data(project, k, v)
    if shots:
        generate_edit_data(p, shots)


fetch_and_save_context()
fetch_and_save_people_avatars()

for p in fetch_user_context()['projects']:
    save_project_data(p)
    fetch_and_save_casting(p)



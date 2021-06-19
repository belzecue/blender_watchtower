#!/usr/bin/env python3

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
BASE_URL = env_vars['KITSU_API']
JWT = env_vars['JWT']

HEADERS = {'headers': {'Authorization': f"Bearer {JWT}"}}

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


def hex_to_rgba(hex):
    color = hex.lstrip('#')
    color = [int(color[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    color.append(1.0)
    return color


def fetch_and_save_image(src_url, dst, force=False):
    if not os.path.exists(dst) or force:
        r = requests.get(src_url, **HEADERS, allow_redirects=True)
        open(dst, 'wb').write(r.content)


def fetch_people():
    r_people = requests.get(f"{BASE_URL}/data/persons", **HEADERS)

    people = []
    # Ensure that public/pictures/thumbnails/persons/ exists
    pathlib.Path('public/pictures/thumbnails/persons').mkdir(parents=True, exist_ok=True)
    for person in r_people.json():
        profile_picture_path = f"pictures/thumbnails/persons/{person['id'] if person['has_avatar'] else 'placeholder'}.png"
        people.append({
            'name': person['full_name'],
            'id': person['id'],
            'profilePicture': profile_picture_path,
            'color': random.choice(COLORS_PALETTE),
        })
        if profile_picture_path:
            src = f"{BASE_URL}/pictures/thumbnails/persons/{person['id']}.png"
            fetch_and_save_image(src, f"public/{profile_picture_path}")
    return people


def fetch_sequences():
    r_sequences = requests.get(f"{BASE_URL}/data/sequences", **HEADERS)
    sequences = []
    for sequence in r_sequences.json():
        sequences.append({'name': sequence['name'], 'id': sequence['id']})
    return sequences


def fetch_task_types():
    r_task_types = requests.get(f"{BASE_URL}/data/task-types", **HEADERS)
    r_task_types = r_task_types.json()
    if 'error' in r_task_types:
        print(r_task_types['message'])
        exit()
    task_types = []
    for task in r_task_types:
        if not task['for_shots']:
            continue
        color = hex_to_rgba(task['color'])

        task_types.append({'name': task['name'], 'color': color, 'id': task['id']})
    return task_types


def fetch_task_statuses():
    r_task_statuses = requests.get(f"{BASE_URL}/data/task-status", **HEADERS)
    task_statuses = []
    for task in r_task_statuses.json():
        color = hex_to_rgba(task['color'])

        task_statuses.append({'name': task['name'], 'color': color, 'id': task['id']})
    return task_statuses


def fetch_shots_and_previews(force=False):
    r_shots = requests.get(f"{BASE_URL}/data/shots/with-tasks", **HEADERS)
    parsed_shots = []

    for shot in r_shots.json():
        print(f"Processing shot {shot['name']}")
        dst = f"public/preview-files/{shot['preview_file_id']}.png"
        # If thumbnail is not found locally, download it
        src_url = f"{BASE_URL}/pictures/thumbnails/preview-files/{shot['preview_file_id']}.png"
        fetch_and_save_image(src_url, dst)
        # Format data as expected by edit breakdown
        tasks = []
        for task in shot['tasks']:
            tasks.append({
                'task_status_id': task['task_status_id'],
                'task_type_id': task['task_type_id'],
                'assignees': task['assignees'],
            })
        parsed_shots.append({
            'name': shot['name'],
            'thumbnailFile': dst.replace('public/', ''),
            'startFrame': shot['data']['frame_in'],
            'durationSeconds': (shot['data']['frame_out'] - shot['data']['frame_in']) / shot['data']['fps'],
            'tasks': tasks,
            'sequence_id': shot['sequence_id'],
        })

    return parsed_shots


def build_edit_data():
    edit_data = {
        'sourceBase': 'http://eb.local:8080/',
        'sourceName': 'sf-edit-v101.mp4',
        'sourceType': 'video/mp4',
        'totalFrames': 14696,
        'frameOffset': 100,
        'fps': 24,
        'taskTypes': fetch_task_types(),
        'taskStatuses': fetch_task_statuses(),
        'shots': fetch_shots_and_previews(),
        'sequences': fetch_sequences(),
        'users': fetch_people(),
    }
    with open('public/edit.json', 'w') as outfile:
        json.dump(edit_data, outfile, indent=2)


build_edit_data()

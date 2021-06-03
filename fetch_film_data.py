#!/usr/bin/env python3

import json
import os.path
import requests


def get_env_data_as_dict(path: str) -> dict:
    with open(path, 'r') as f:
       return dict(tuple(line.replace('\n', '').split('=')) for line
                in f.readlines() if not line.startswith('#'))


env_vars = get_env_data_as_dict('.env.local')
BASE_URL = env_vars['KITSU_API']
JWT = env_vars['JWT']

HEADERS = {'headers': {'Authorization': f"Bearer {JWT}"}}


def hex_to_rgba(hex):
    color = hex.lstrip('#')
    color = [int(color[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    color.append(1.0)
    return color


def fetch_sequences():
    r_sequences = requests.get(f"{BASE_URL}/data/sequences", **HEADERS)
    sequences = []
    for sequence in r_sequences.json():
        sequences.append({'name': sequence['name'], 'id': sequence['id']})
    return sequences


def fetch_task_types():
    r_task_types = requests.get(f"{BASE_URL}/data/task-types", **HEADERS)
    task_types = []
    for task in r_task_types.json():
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
        save_path = f"public/preview-files/{shot['preview_file_id']}.png"
        # If thumbnail is not found locally, download it
        if not os.path.exists(save_path) or force:
            url = f"{BASE_URL}/pictures/thumbnails/preview-files/{shot['preview_file_id']}.png"
            r = requests.get(url, **HEADERS, allow_redirects=True)
            open(save_path, 'wb').write(r.content)
        # Format data as expected by edit breakdown
        tasks = []
        for task in shot['tasks']:
            tasks.append({
                'task_status_id': task['task_status_id'],
                'task_type_id': task['task_type_id'],
            })
        parsed_shots.append({
            'name': shot['name'],
            'thumbnailFile': save_path.replace('public/', ''),
            'startFrame': shot['data']['frame_in'],
            'durationSeconds': (shot['data']['frame_out'] - shot['data']['frame_in']) / shot['data']['fps'],
            'scene': shot['sequence_name'],
            'tasks': tasks,
            'sequence_id': shot['sequence_id'],
        })

    return parsed_shots


def build_edit_data():
    edit_data = {
        'sourceBase': 'http://eb.local:8080/',
        'sourceName': 'sf-edit-v097.mp4',
        'sourceType': 'video/webm',
        'totalFrames': 14741,
        'frameOffset': 101,
        'fps': 24,
        'taskTypes': fetch_task_types(),
        'taskStatuses': fetch_task_statuses(),
        'shots': fetch_shots_and_previews(),
        'sequences': fetch_sequences(),
    }
    with open('public/edit-review.json', 'w') as outfile:
        json.dump(edit_data, outfile, indent=2)


build_edit_data()

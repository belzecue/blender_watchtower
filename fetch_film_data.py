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


def fetch_sequences():
    r_sequences = requests.get(f"{BASE_URL}/data/sequences", **HEADERS)
    with open('public/sequences.json', 'w') as outfile:
        json.dump(r_sequences, outfile, indent=2, sort_keys=True)


def fetch_shots_and_previews(force=False):
    r_shots = requests.get(f"{BASE_URL}/data/shots", **HEADERS)
    parsed_shots = []

    for shot in r_shots.json():
        save_path = f"public/preview-files/{shot['preview_file_id']}.png"
        # If thumbnail is not found locally, download it
        if not os.path.exists(save_path) or force:
            url = f"{BASE_URL}/pictures/thumbnails/preview-files/{shot['preview_file_id']}.png"
            r = requests.get(url, **HEADERS, allow_redirects=True)
            open(save_path, 'wb').write(r.content)
        # Format data as expected by edit breakdown
        parsed_shots.append({
            'name': shot['name'],
            'thumbnailFile': save_path.replace('public/', ''),
            'startFrame': shot['data']['frame_in'],
            'durationSeconds': (shot['data']['frame_out'] - shot['data']['frame_in']) / shot['data']['fps'],
            'scene': shot['sequence_name']
        })

    with open('public/shots.json', 'w') as outfile:
        json.dump(parsed_shots, outfile, indent=2, sort_keys=True)


fetch_shots_and_previews()

# Watchtower

Interactive film production management tool. Watchtower allows you to see the big picture of a 
short film or episode and unpack as much information as needed, down to the duration of a shot and
assets used in it. All in the space of one screen.

## Features

* Grid view (for shots and assets) with grouping and filtering tools
* Detail view
* Timeline showing individual shots as well as task statuses
* Compatible with zou as data backend


## Project setup
```
yarn install
```

Watchtower is a Vue application. It can be managed through the [vue-cli package](https://cli.vuejs.org/).

### Populate with data

* Have access to the API of a working Zou (and optionally Kitsu) installation
* Make sure you have `ffmpeg` installed in your system. It's needed for video stats generation.
* Place an export of the film in the `public` directory, and name it `edit.mp4`. If possible, choose
encoder settings that make it possible to easily scrub the video.
* Create an `env.local` file and set the required env variables
* Run the `fetch_film_data.py` script. The script will connect to a zou instance, query for the needed information and 
  create a couple of files in `public`: 
  * `edit.json`: containing all the data required by watchtower
  * `pictures`: containing user profile thumbnails
  * `preview-files`: containing shot and asset thumbnails
* At this point it's possible to run Watchtower and check the status of your production

### Compiles and hot-reloads for development
```
yarn serve
```

### Lints and fixes files
```
yarn lint
```

### Run in production
Use `yarn build` to create a build that can be deployed on a production server. The application can be served as a
static website. Follow the steps in "Populate with data" to provide Watchtower with data to display.


## TODOS

* Implement Kitsu-compatible authentication
* Support multiple projects (with users, etc.)
* Allow edits
  * Update task assignations
  * Asset casting
* Snapshotting (to compare the state of the edit/tasks over time)

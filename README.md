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
* Create an `env.local` file (see the example one) and set the required env variables
* Run the `fetch_data_from_kitsu.py` script. The script will connect to a zou instance, query for the needed information 
  and create a few files in the `public` directory: 
  * `static-projects`: containing all the data required by watchtower
  * `static-previews`: containing shot and asset thumbnails
* At this point it's possible to run Watchtower and check the status of your production
* For each project it's currently necessary to manually place an `edit.mp4`file in `static-projects/<project-id>/`

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

* Allow edits
  * Update task assignations
  * Asset casting
* Snapshotting (to compare the state of the edit/tasks over time)

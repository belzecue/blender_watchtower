<template>
  <div class="container is-fluid p-0">
    <Toolbar
        @set-current-project-id="setCurrentProjectId"
        :projects="projectsFromContext"
        :current-project-id="currentProjectId" />
    <div class="columns is-gapless">
      <div class="column is-two-thirds">
        <ThumbnailView
            @set-current-frame="setCurrentFrame"
            @set-selected-assets="setSelectedAssets"
            :taskTypes="taskTypes"
            :taskStatuses="taskStatuses"
            :users="users"
            :sequences="sequences"
            :shots="shots"
            :assets="assets"
            :assetTypes="assetTypes"
            :current-frame="currentFrame"
            :fps="fps"
            :timeline-visible-frames="timelineVisibleFrames"
            :selected-assets="selectedAssets"
        />
      </div>
      <div class="column">
        <VideoPlayer
            @set-current-frame="setCurrentFrame"
            @playback-status-updated="setIsPlaying"
            :is-playing="isPlaying"
            :current-frame="currentFrame"
            :frame-offset="frameOffset"
            :fps="fps"
            :options="videoPlayerOptions" />
        <div>Frame {{ currentFrame }}</div>
        <div v-if="currentSequence" >Sequence {{ currentSequence.name }}</div>
        <div v-if="currentShot" >Shot {{ currentShot.name }}</div>
      </div>
    </div>
    <div class="columns is-gapless">
      <div class="column is-full">
        <TimelineView
            @set-current-frame="setCurrentFrame"
            @set-timeline-visible-frames="setTimelineVisibleFrames"
            :taskTypes="taskTypes"
            :taskStatuses="taskStatuses"
            :sequences="sequences"
            :shots="shots"
            :current-frame="currentFrame"
            :total-frames="totalFrames"
            :fps="fps"
            :selected-assets="selectedAssets"
        />
      </div>
    </div>
  </div>
</template>

<script>

import VideoPlayer from "@/components/VideoPlayer";
import ThumbnailView from "@/components/ThumbnailView";
import TimelineView from "@/components/TimelineView";
import Toolbar from "@/components/Toolbar";

import colors from '@/lib/colors'
import dataurls from "@/lib/dataurls";

export default {
  name: "MainView",
  components: {
    VideoPlayer,
    ThumbnailView,
    TimelineView,
    Toolbar,
  },
  props: {
    currentUser: {type: Object},
    context: {type: Object},
  },
  data () {
    return {
      // Project id as a string
      currentProjectId: this.$route.params.projectId,
      // Query data
      taskTypes: [],
      taskStatuses: [],
      users: [],
      sequences: [],
      shots: [],
      assets: [],
      assetTypes: [],
      totalFrames: 1,
      frameOffset: 0,
      fps: 24,
      videoPlayerOptions: null,
      // Runtime state
      isPlaying: false,
      currentFrame: 0,
      timelineVisibleFrames: [0, 1],
      currentSequence: null,
      currentShot: null,
      selectedAssets: [],
    }
  },
  computed: {
    projectsFromContext: function () {
      if (!this.context) {return []}
      return this.context.projects
    }
  },
  methods: {
    setCurrentFrame: function (frameNumber) {
      // Force frameNumber to be int. Since it comes from JSON metadata it could have
      // accidentally been stored as a string. This is due to weak schema validation on Kitsu.
      this.currentFrame = parseInt(frameNumber);

      // Find the shot for the current frame (not necessarily visible as a thumbnail).
      let shotForCurrentFrame = null;
      for (const shot of this.shots) {
        if (shot.startFrame > this.currentFrame) {
          break;
        }
        shotForCurrentFrame = shot;
      }
      this.currentShot = shotForCurrentFrame;

      // Find the corresponding sequence, if any.
      let currSequence = null;
      if (shotForCurrentFrame) {
        for (const seq of this.sequences) {
          if (seq.id === shotForCurrentFrame.sequence_id) {
            currSequence = seq;
            break;
          }
        }
      }
      this.currentSequence = currSequence;
    },
    setSelectedAssets: function (assets) {
      this.selectedAssets = assets;
    },
    setTimelineVisibleFrames: function (frameRange) {
      this.timelineVisibleFrames = frameRange;
    },
    setIsPlaying: function (value) {
      this.isPlaying = value;
    },
    togglePlayback: function () {
      this.isPlaying = !this.isPlaying;
    },
    handleHotkey: function (event) {
      if (event.isComposing || event.key === " ") {
        this.togglePlayback();
      }
    },
    setCurrentProjectId: function (value) {
      this.currentProjectId = value;
      this.initWithProject(value);
    },
    fetchProjectSequences: function (projectId) {
      // let url = `static-projects/${projectId}/sequences.json`
      let url = dataurls.getUrl('sequences', projectId)
      fetch(url)
        .then(response => response.json())
        .then(data => {
          // Setup data for Sequences.
          for (let i = 0; i < data.length; i++) {
            let seq = data[i];
            seq.color = colors.paletteDefault[i];
          }
          this.sequences = data;

          // Perform asset casting
          for (let i = 0; i < this.sequences.length; i++) {
            let seq = data[i];
            this.fetchSequenceCasting(projectId, seq.id)
          }
        })
    },
    fetchProjectShots: function (projectId) {
      // let url = `static-projects/${projectId}/shots.json`
      let url = dataurls.getUrl('shots', projectId)
      fetch(url)
        .then(response => response.json())
        .then(data => {
          // Setup data for Shots.
          for (let shot of data) {
            // If the shot comes from Kitsu, we need to add some properties.
            if (!dataurls.isStatic()) {
              shot.thumbnailUrl = `/api/pictures/thumbnails/preview-files/${shot.preview_file_id}.png`;
              shot.startFrame = shot.data.frame_in;
              shot.durationSeconds = (shot.data.frame_out - shot.data.frame_in) / this.fps;
            }
            shot.assets = [];
          }
          this.shots = data;
          this.shots.sort((a, b) => (a.startFrame > b.startFrame) ? 1 : -1)
        })
    },
    fetchProjectAssets: function (projectId) {
      let url = dataurls.getUrl('assets', projectId)
      fetch(url)
        .then(response => response.json())
        .then(data => {
          // Setup data for Assets.
          for (let asset of data) {
            if (!dataurls.isStatic()) {
              // If the shot comes from Kitsu, we need to add the thumbnailUrl property.
              asset.thumbnailUrl = `/api/pictures/thumbnails/preview-files/${asset.preview_file_id}.png`;
            }
            asset.shots = [];
          }
          this.assets = data;
        })
    },
    fetchSequenceCasting: function (projectId, sequenceId) {
      let url = dataurls.getUrl('casting', projectId, sequenceId)
      fetch(url)
        .then(response => response.json())
        .then(data => {
          // Index casting relations.
          // Object.entries(data.casting).forEach(([shotId, assets]) => {
          for (const [shotId, assets] of Object.entries(data)) {
            for (let shot of this.shots) {
              if (shot.id === shotId) {
                // Add assets to shot.
                shot.assets = assets;

                // Add shot to each of the assets.
                for (let asset_cast of assets) {
                  for (let asset of this.assets) {
                    if (asset.id === asset_cast.asset_id) {
                      asset.shots.push(shotId);
                      break;
                    }
                  }
                }
                break;
              }
            }
          }
        })
    },
    fetchEditData: function (projectId) {
      let urlEdit = `static-projects/${projectId}/edit.json`
      fetch(urlEdit)
        .then(response => response.json())
        .then(data => {
          this.totalFrames = data.totalFrames;
          this.frameOffset = data.frameOffset;
          this.videoPlayerOptions = {
            autoplay: false,
            controls: true,
            preload: 'auto',
            sources: [
              {
                src: data.sourceName,
                type: data.sourceType,
              }
            ]
          };
          this.setCurrentFrame(data.frameOffset);
        })
    },
    fetchProjectData: function (projectId) {
      // Load edit data (to be fetched from a web API later)
      let urlProject = dataurls.getUrl('project', projectId)
      fetch(urlProject)
        .then(response => response.json())
        .then(data => {
          if (data.task_types.length > 0) {
            this.taskTypes = this.taskTypes.filter(function(t) {
              return data.task_types.includes(t.id);
            });
          }
          if (data.task_statuses.length > 0) {
            this.taskStatuses = this.taskStatuses.filter(function(t) {
              return data.task_statuses.includes(t.id);
            });
          }
          if (data.asset_types.length > 0) {
            this.assetTypes = this.assetTypes.filter(function(a) {
              return data.asset_types.includes(a.id);
            });
          }
          if (data.team.length > 0) {
            let filteredUsers = this.users.filter(function(u) {
              return data.team.includes(u.id);
            });

            let processedUsers = [];

            for (let i = 0; i < filteredUsers.length; i++) {
              let filteredUser = filteredUsers[i];
              let user = {
                name: filteredUser.full_name,
                id: filteredUser.id,
                color: filteredUser.color,
                profilePicture: `static-previews/pictures/thumbnails/persons/${filteredUser.id}.png`
              };
              processedUsers.push(user);
            }
            this.users = processedUsers;
            colors.batchAssignColor(this.users);
          }

        })
      },
    initWithProject: function (projectId) {
      fetch(dataurls.getUrl('context'))
        .then(response => response.json())
        .then(data => {
          // Extend the asset_types context with a color attribute
          colors.batchAssignColor(data.asset_types);
          this.assetTypes = data.asset_types;

          colors.batchConvertColorHexToRGB(data.task_types);
          this.taskTypes = data.task_types;

          colors.batchConvertColorHexToRGB(data.task_status);
          this.taskStatuses = data.task_status;

          this.users = data.persons;

          this.fetchProjectData(projectId);
          this.fetchProjectSequences(projectId);
          this.fetchProjectShots(projectId);
          this.fetchProjectAssets(projectId);
          this.fetchEditData(projectId);
        })
    }
  },
  unmounted () {
    document.body.removeEventListener('keydown', this.handleHotkey);
  },
  mounted() {
    // Global listener for any key pressed while the document is in focus
    document.body.addEventListener('keydown', this.handleHotkey);
    this.initWithProject(this.$route.params.projectId);
  },
}
</script>

<style scoped>
  h3 {
    margin: 40px 0 0;
  }
  ul {
    list-style-type: none;
    padding: 0;
  }
  li {
    display: inline-block;
    margin: 0 10px;
  }
  a {
    color: #42b983;
  }
  canvas {
    border: 2px solid black;
    background-color: black;
  }
</style>

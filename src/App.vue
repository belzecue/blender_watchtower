<template>
  <div class="container is-fluid p-0">
    <Toolbar />
    <div class="columns is-gapless">
      <div class="column is-two-thirds">
        <ThumbnailView
            @set-current-frame="setCurrentFrame"
            :taskTypes="taskTypes"
            :taskStatuses="taskStatuses"
            :users="users"
            :sequences="sequences"
            :shots="shots"
            :current-frame="currentFrame" />
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
        <div> Frame {{ currentFrame }}</div>
        <div>Properties editor</div>
      </div>
    </div>
    <div class="columns is-gapless">
      <div class="column is-full">
        <TimelineView
            @set-current-frame="setCurrentFrame"
            :taskTypes="taskTypes"
            :taskStatuses="taskStatuses"
            :sequences="sequences"
            :shots="shots"
            :current-frame="currentFrame"
            :total-frames="totalFrames"
            :fps="fps"
        />
      </div>
    </div>

  </div>
</template>

<script>
import VideoPlayer from "./components/VideoPlayer.vue";
import ThumbnailView from "./components/ThumbnailView.vue";
import TimelineView from "./components/TimelineView.vue";
import Toolbar from  "./components/Toolbar.vue";

export default {
  name: 'App',
  components: {
    VideoPlayer,
    ThumbnailView,
    TimelineView,
    Toolbar,
  },
  data () {
    return {
      isPlaying: false,
      taskTypes: [],
      taskStatuses: [],
      users: [],
      sequences: [],
      shots: [],
      currentFrame: 0,
      totalFrames: 1,
      frameOffset: 0,
      fps: 24,
      videoPlayerOptions: null,
    }
  },
  methods: {
    setCurrentFrame: function (frame) {
      this.currentFrame = frame
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
    }
  },
  unmounted () {
    document.body.removeEventListener('keydown', this.handleHotkey);
  },
  mounted() {
    // Global listener for any key pressed while the document is in focus
    document.body.addEventListener('keydown', this.handleHotkey);

    // Load edit data (to be fetched from a web API later)
    fetch('edit.json')
      .then(response => response.json())
      .then(data => {
        const colorPalette = [
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
          [0.5555555555555555, 0.5555555555555555, 0.5555555555555555, 1.0],
        ];

        // Setup data for Sequences.
        for (let i = 0; i < data.sequences.length; i++) {
          let seq = data.sequences[i];
          seq.color = colorPalette[i];
        }
        this.sequences = data.sequences;

        // Setup data for Shots.
        for (let shot of data.shots) {
          shot.thumbnailUrl = data.sourceBase + shot.thumbnailFile;
        }
        this.shots = data.shots;
        this.shots.sort((a, b) => (a.startFrame > b.startFrame) ? 1 : -1)

        // Copy the rest of the data.
        this.taskTypes = data.taskTypes;
        this.taskStatuses = data.taskStatuses;
        this.users = data.users;
        this.totalFrames = data.totalFrames;
        this.frameOffset = data.frameOffset;
        this.fps = data.fps;

        // Initialize the video player.
        this.videoPlayerOptions = {
          autoplay: false,
          controls: true,
          preload: 'auto',
          sources: [
            {
              src: data.sourceBase + data.sourceName,
              type: data.sourceType,
            }
          ]
        };

        // Set the playhead at the first available frame.
        this.setCurrentFrame(data.frameOffset);
      })
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

<template>
  <div class="container is-fluid">
    <h1>Edit Breakdown Web</h1>
    <div class="columns">
      <div class="column is-two-thirds">
        <ThumbnailView @set-current-frame="setCurrentFrame" :shots="shots" :current-frame="currentFrame"/>
      </div>
      <div class="column">
        <VideoPlayer @set-current-frame="setCurrentFrame" :current-frame="currentFrame" :options="videoPlayerOptions" />
        <div> Frame {{ currentFrame }}</div>
        <div>Properties editor</div>
      </div>
    </div>
    <div class="columns is-gapless">
      <div class="column is-full">
        <TimelineView @set-current-frame="setCurrentFrame" :current-frame="currentFrame" :total-frames="totalFrames"/>
      </div>
    </div>

  </div>
</template>

<script>
import VideoPlayer from "./components/VideoPlayer.vue";
import ThumbnailView from "./components/ThumbnailView.vue";
import TimelineView from "./components/TimelineView.vue";

export default {
  name: 'App',
  components: {
    VideoPlayer,
    ThumbnailView,
    TimelineView,
  },
  data () {
    return {
      shots: [],
      currentFrame: 0,
      videoPlayerOptions: null,
      totalFrames: null,
    }
  },
  methods: {
    setCurrentFrame: function (frame) {
      this.currentFrame = frame
    }
  },
  mounted() {
    fetch('edit.json')
      .then(response => response.json())
      .then(data => {
        for (let i = 0; i < data.shots.length; i++) {
          let parsedShot = data.shots[i];
          parsedShot.thumbnailUrl = data.sourceBase + 'thumbnails/' + parsedShot.thumbnailFile;
          this.shots.push(parsedShot)
        }

        this.shots = data.shots;
        this.totalFrames = data.totalFrames;
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

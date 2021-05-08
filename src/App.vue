<template>
  <div class="container is-fluid">
    <h1>Edit Breakdown Web</h1>
    <div class="columns">
      <div class="column is-two-thirds">
        <ThumbnailView />
      </div>
      <div class="column">
        <VideoPlayer @set-current-frame="setCurrentFrame" :options="videoOptions" />
        <div> Frame {{ currentFrame }}</div>
        <div>Properties editor</div>
      </div>
    </div>
    <div class="columns is-gapless">
      <div class="column is-full">
        <TimelineView :current-frame="currentFrame"/>
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
      currentFrame: 0,
      videoOptions: {
        autoplay: true,
        controls: true,
        sources: [
          {
            src:
              "/spring.mp4",
              type: "video/mp4"
          }
        ]
      }
    }
  },
  methods: {
    setCurrentFrame: function (frame) {
      this.currentFrame = frame
    }
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

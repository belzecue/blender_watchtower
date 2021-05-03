<template>
  <div class="container">
    <h1>{{ msg }}</h1>
    <div class="columns">
      <div class="column is-two-thirds">
        <thumbnail-view></thumbnail-view>
      </div>
      <div class="column">
        <video-player :options="videoOptions"/>
        <div>Properties editor</div>
      </div>
    </div>
    <div class="columns">
      <div>Timeline</div>
    </div>

  </div>
</template>

<script>

import VideoPlayer from "./VideoPlayer.vue";
import ThumbnailView from "./ThumbnailView";

export default {
  name: 'EditBreakdown',
  components: {
    VideoPlayer,
    ThumbnailView
  },
  props: {
    msg: String
  },
  data() {
    return {
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
    };
  }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
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

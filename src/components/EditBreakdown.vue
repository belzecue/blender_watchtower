<template>
  <div class="hello">
    <h1>{{ msg }}</h1>
    <video-player :options="videoOptions"/>
  </div>
</template>

<script>

import VideoPlayer from "./VideoPlayer.vue";

export default {
  name: 'EditBreakdown',
  components: {
    VideoPlayer
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
</style>

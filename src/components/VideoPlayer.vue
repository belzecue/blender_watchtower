<template>
  <div>
    <video ref="videoPlayer" class="video-js vjs-fluid"></video>
  </div>
</template>

<script>
import videojs from 'video.js';
import './../../node_modules/video.js/dist/video-js.css'

export default {
  name: "VideoPlayer",
  props: {
    options: {
      type: Object,
      default() {
          return {};
      }
    }
  },
  data() {
    return {
      player: null
    }
  },
  mounted() {
    this.player = videojs(this.$refs.videoPlayer, this.options, function onPlayerReady() {
      console.log('onPlayerReady', this);
    })
  },
  beforeDestroy() {
    if (this.player) {
      this.player.dispose()
    }
  }
}
</script>

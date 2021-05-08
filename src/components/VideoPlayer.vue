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
  methods: {
    setCurrentFrame: function () {
      if (!this.player) {return}
      let currentTime = this.player.currentTime()
      this.$emit('set-current-frame', currentTime)
      this.animationFrameQueue = this.player.requestAnimationFrame(this.setCurrentFrame)
    },
    cancelSetCurrentFrame: function () {
      this.player.cancelAnimationFrame(this.animationFrameQueue)
    }
  },
  data() {
    return {
      player: null,
      animationFrameQueue: null
    }
  },
  mounted() {
    this.player = videojs(this.$refs.videoPlayer, this.options, function onPlayerReady() {
      console.log('onPlayerReady', this);
    })
    this.player.on('play', this.setCurrentFrame)
    this.player.on('pause', this.cancelSetCurrentFrame)
  },
  beforeDestroy() {
    if (this.player) {
      this.player.dispose()
    }
  }
}
</script>

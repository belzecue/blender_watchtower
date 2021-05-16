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
    currentFrame: Number,
    isPlaying: Boolean,
    options: {
      type: Object,
      default() {
          return {};
      }
    }
  },
  data() {
    return {
      player: null,
      animationFrameQueue: null,
    }
  },
  watch: {
    isPlaying: function () {
      if (this.isPlaying) {
        this.player.play();
      } else {
        this.player.pause();
      }
    },
    currentFrame: function () {
      // this.player.currentTime(this.currentFrame / 24000)
      if (! this.player.paused()) {return}
      let currentTime = this.currentFrame / 24;
      this.player.currentTime(currentTime);
    },
    options: function () {
      if (this.player) {this.player.dispose()}
      this.player = videojs(this.$refs.videoPlayer, this.options, function onPlayerReady() {
        console.log('Player is ready');
      })
      this.player.on('play', this.setCurrentFrameAndRequestAnimationFrame);
      // Update global isPlaying status
      this.player.on('play', () => {this.$emit('playback-status-updated', true)});
      this.player.on('pause', this.cancelSetCurrentFrame);
      // Update global isPlaying status
      this.player.on('pause', () => {this.$emit('playback-status-updated', false)});
      this.player.on('seeking', this.setCurrentFrame);
    },
  },
  methods: {
    setCurrentFrame: function () {
      if (!this.player) {return}
      let currentFrame = this.player.currentTime() * 24;
      this.$emit('set-current-frame', Math.round(currentFrame));
    },
    setCurrentFrameAndRequestAnimationFrame: function () {
      if (!this.player) {return}
      this.setCurrentFrame();
      this.animationFrameQueue = this.player.requestAnimationFrame(this.setCurrentFrameAndRequestAnimationFrame);
    },
    cancelSetCurrentFrame: function () {
      this.player.cancelAnimationFrame(this.animationFrameQueue);
    }
  },
  beforeDestroy() {
    if (this.player) {
      this.player.dispose();
    }
  }
}
</script>

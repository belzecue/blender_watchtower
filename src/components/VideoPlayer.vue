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
    frameOffset: Number,
    fps: Number,
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
      // If the player is not ready, or it is currently playing, do nothing.
      if (!this.player || !this.player.paused()) {
        return;
      }

      // Limit frame value to 0 or greater
      let currentTime = Math.max(0, (this.currentFrame - this.frameOffset) / this.fps);
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
      let currentFrame = this.player.currentTime() * this.fps + this.frameOffset;
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

<style>
  .vjs-paused .vjs-big-play-button {
    display: none;
  }
</style>

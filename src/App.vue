<template>
  <div id="app">
    <EditBreakdown @set-current-frame="setCurrentFrame" :current-frame="currentFrame" msg="Edit Breakdown Web"/>
  </div>
</template>

<script>
import EditBreakdown from './components/EditBreakdown.vue'

export default {
  name: 'App',
  components: {
    EditBreakdown
  },
  data: function () {
    return {
      currentFrame: 0,
    }
  },
  methods: {
    setCurrentFrame: function (frame) {
      this.currentFrame = frame
    }
  }
}
</script>

<style>
</style>

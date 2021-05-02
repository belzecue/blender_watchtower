<template>
  <div id="app">
    <EditBreakdown msg="Edit Breakdown Web"/>
  </div>
</template>

<script>
import EditBreakdown from './components/EditBreakdown.vue'

export default {
  name: 'App',
  components: {
    EditBreakdown
  }
}
</script>

<style>
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
  color: #2c3e50;
  margin-top: 60px;
}
</style>

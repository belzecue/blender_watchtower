<template>
  <div class="app-container">
    <Toolbar/>
    <div class="dashboard">
      <h2>About</h2>
      <p>Interactive film production management tool. Watchtower allows you to see the big picture of a short film or episode and unpack as much information as needed, down to the duration of a shot and assets used in it. All in the space of one screen.</p>
      <p>Originally developed during the production of <a href="https://www.youtube.com/watch?v=_cMxraX_5RE">Sprite Fright</a>. More info at <a href="https://studio.blender.org">studio.blender.org</a>.</p>
    </div>
  </div>
</template>

<script>
import Toolbar from "@/components/Toolbar";

export default {
  name: "About",
  components: {Toolbar},
  props: {
    currentUser: {type: Object,},
    context: {type: Object}
  },
}
</script>

<style scoped>
.dashboard {
  background-color: var(--panel-bg-color);
  border-radius: var(--border-radius);
  margin: var(--spacer-3) auto;
  padding: 0 var(--spacer-3);
  width: 50%;
}
</style>

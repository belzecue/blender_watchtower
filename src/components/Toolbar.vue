<template>
  <div class="app-toolbar">
    <span>Watchtower</span>
    <select v-if="projects" @change="switchToProject" v-model="currentProjectSelected" class="ml-4 mt-2">
      <option v-for="project in projects" :key="project.id" :value="project.id">
        {{ project.name }}
      </option>
    </select>
  </div>
</template>

<script>
export default {
  name: "Toolbar",
  props: {
    projects: {type: Array},
    currentProjectId: {type: String}
  },
  data () {
    return {
      currentProjectSelected: this.currentProjectId
  }},
  methods: {
    switchToProject(event) {
      this.$router.push({ name: 'pro', params: { projectId: event.target.value } })
      this.$emit('set-current-project-id', event.target.value)
    }
  }
}
</script>

<style scoped>

</style>

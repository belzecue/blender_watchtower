<template>
  <div class="app-toolbar">
    <select v-if="projects" @change="switchToProject" v-model="currentProjectSelected" class="ml-4 mt-2">
      <option v-for="project in projects" :key="project.id" :value="project.id">
        {{ project.name }}
      </option>
    </select>
    <div class="app-links">
      <ul>
        <li><a href="/#/" title="Dashboard">Dashboard</a></li>
        <li><a href="/about" title="About Watchtower">About Watchtower</a></li>
      </ul>
    </div>
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
.app-links {
  margin-left: auto;
}

.app-links > ul {
  display: flex;
  list-style: none;
  margin: 0;
  padding: 0;
}

.app-links ul > li {
  margin-left: var(--spacer-2)
}

.app-links a {
  color: var(--text-color-hint)
}
</style>

<template>
  <div class="app-container">
    <Toolbar/>
    <div class="dashboard">
      <h2>Dashboard</h2>
      <p>Your projects:</p>
      <ul v-if="context" class="projects-list">
        <li v-for="project in context.projects" :key="project.id">
          <router-link :to="{ name: 'pro', params: { projectId: project.id }}">
            <img :src="project.thumbnailUrl" :alt="project.name" class="project-thumbnail" />
            <h3>{{ project.name }}</h3>
          </router-link>
        </li>
      </ul>
    </div>
  </div>
</template>

<script>
import Toolbar from "@/components/Toolbar";
export default {
  name: "Dashboard",
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
  margin: var(--spacer-3);
  padding: 0 var(--spacer-3);
}

.projects-list {
  list-style-type: none;
  padding: 0;
}

.projects-list li {
  border-bottom: var(--border-width) var(--border-color) solid;
  margin-bottom: var(--spacer-2);
  padding-bottom: var(--spacer-2);
}

.projects-list li:last-child {
  border-bottom: none;
  margin-bottom: 0;
  padding-bottom: 0;
}

.projects-list li > a {
  align-items: center;
  border-radius: var(--border-radius);
  display: flex;
  font-weight: normal;
  text-decoration: none;
  transition: color var(--transition-speed) ease-in-out, background-color var(--transition-speed) ease-in-out;
}

.projects-list li > a:hover {
  background-color: var(--panel-bg-color-highlight);
}

.projects-list li > a:hover .project-thumbnail {
  transform: scale(1.1);
}

.project-thumbnail {
  border-radius: var(--border-radius);
  height: 32px;
  margin: 0 var(--spacer-3);
  transition: transform var(--transition-speed) ease-in-out;
  width: 32px;
}
</style>

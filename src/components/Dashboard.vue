<template>
  <div class="app-container">
    <Toolbar/>
    <p>Landing dashboard, pick a project here.</p>
    <ul v-if="context">
      <li v-for="project in context.projects" :key="project.id">
        <router-link :to="{ name: 'pro', params: { projectId: project.id }}">{{ project.name }}</router-link>
        <img :src="project.thumbnailUrl" alt="Project preview" />
      </li>
    </ul>

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

</style>

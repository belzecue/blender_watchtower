<template>
  <router-view
      :currentUser="currentUser"
      :context="context"
  />
</template>
<script>

import dataurls from "@/lib/dataurls";

export default {
  name: 'App',
  data () {
    return {
      currentUser: {
        isAuthenticated: false,
        role: null // Not used for now
      },
      context: null,
    }
  },
  mounted() {
    // Use live API or static data dump
    fetch(dataurls.getUrl('context'))
    .then(response => response.json())
    .then(data => {
      this.context = {}
      for (let project of data.projects) {
        if (!dataurls.isStatic) {
          project.thumbnailUrl = `/api/pictures/thumbnails/projects/${project.id}.png`;
        }
      }
      this.context.projects = data.projects;
    })
  }
}

</script>

<style scoped>

</style>

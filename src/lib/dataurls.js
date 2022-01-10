export default {
  isStatic () {
    return process.env.VUE_APP_DATA_SOURCE === 'static';
  },
  getUrl (name, projectId, sequenceId) {

    let projectQueryParams = new URLSearchParams({project_id: projectId}).toString();

    switch(name) {
      case 'context':
        return (this.isStatic() ?
          'context.json' :
          '/api/data/user/context');

      case 'project':
        return (this.isStatic() ?
          `static-projects/${projectId}/project.json` :
          `/api/data/projects/${projectId}`);

      case 'sequences':
        return this.isStatic() ?
           `static-projects/${projectId}/sequences.json` :
           `/api/data/sequences?${projectQueryParams}`

      case 'shots':
        return this.isStatic() ?
           `static-projects/${projectId}/shots.json` :
           `/api/data/shots/with-tasks?${projectQueryParams}`

      case 'assets':
        return this.isStatic() ?
           `static-projects/${projectId}/assets.json` :
           `/api/data/assets/with-tasks?${projectQueryParams}`

      case 'casting':
        return this.isStatic() ?
           `static-projects/${projectId}/sequences/${sequenceId}/casting.json` :
           `/api/data/projects/${projectId}/sequences/${sequenceId}/casting`

    }
  }
}

<template>
  <div id="app">
    <form v-on:submit.prevent="onSubmit">
      <input type="email" name="email" v-model="email">
      <input type="password" name="password" v-model="password">
      <input type="submit" name="submit" value="Login">
    </form>
    <button @click="fetchScenes">Fetch Sequences</button>
  </div>
</template>

<script>
import superagent from 'superagent'

export default {
  name: "LoginForm",
  data () {
    return{
      email: '',
      password: ''
    }
  },
  methods: {
    fetchScenes() {
      console.log(this);
      superagent
        .get('/api/data/sequences')
        .set('Authorization', 'Bearer ' + this.$cookie.get('access_token_cookie'))
        .end((err, res) => {
          console.log(err, res.body)
        })
    },
    onSubmit(){
      const agent = superagent.agent();
      agent
        .post('/api/auth/login')
        .send({
          "email": this.email,
          "password": this.password
        })
        .end((err, res) => {
        if (err) {
          if (res.body.default_password) {
            err.default_password = res.body.default_password
            err.token = res.body.token
          }
        } else {
          if (res.body.login) {
            // const user = res.body.user
            this.$emit('set-is-authenticated', true)
          } else {
            console.log('Could not log in')
          }
        }
      })
    }
  }
}
</script>


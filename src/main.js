import Vue from 'vue'
import App from './App.vue'
import 'buefy/dist/buefy.css'

import VueCookie from 'vue-cookie'
import router from './router'

Vue.config.productionTip = false
Vue.use(VueCookie)

new Vue({
  router,
  render: h => h(App)
}).$mount('#app')

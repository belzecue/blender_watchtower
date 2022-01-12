import Vue from 'vue'
import App from './App.vue'

import VueCookie from 'vue-cookie'
import router from './router'

import './assets/main.css'

Vue.config.productionTip = false
Vue.use(VueCookie)

new Vue({
  router,
  render: h => h(App)
}).$mount('#app')

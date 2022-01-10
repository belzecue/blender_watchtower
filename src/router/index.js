import Vue from 'vue'
import VueRouter from 'vue-router'
import MainView from "@/components/MainView";
import Dashboard from "@/components/Dashboard";
import auth from "@/lib/auth";

Vue.use(VueRouter)


const routes = [
  {
    path: '/',
    name: 'dashboard',
    component: Dashboard,
    beforeEnter: (to, from, next) => {
      if (process.env.VUE_APP_DATA_SOURCE === 'static') {
        next()
        // return
      }

      // Check for logged in status if we use Kitsu as data store
      auth.isServerLoggedIn((err, isLoggedIn) => {
        if (err) {
          next({
            path: '/server-down',
            query: { redirect: to.fullPath }
          })
        } else if (isLoggedIn === undefined) {
          next({
            path: '/login',
            query: { redirect: to.fullPath }
          })
        } else {
          // User is authenticated
          next()
        }
      })
    }
  },
  {
    path: '/pro/:projectId',
    name: 'pro',
    component: MainView,
  }]

const router = new VueRouter({
  // mode: 'history',
  routes
})

export default router

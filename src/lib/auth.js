import superagent from 'superagent'

const auth = {
  isServerLoggedIn (callback) {
    superagent
      .get('/api/auth/authenticated')
      .end((err, res) => {
        if (err && res && [401, 422].includes(res.statusCode)) {
          callback(null)
        } else if (err) {
          callback(err)
        } else if (res && res.body === null) {
          callback(err)
        } else {
          // User is authenticated.
          callback(null, true)
        }
      })
  },
}

export default auth

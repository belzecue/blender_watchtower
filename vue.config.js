module.exports = {
  productionSourceMap: false,
  publicPath: process.env.NODE_ENV === 'production'
    ? '/watchtower/'
    : '/',
  devServer: {
    host: 'localhost',
    proxy: {
      '/api': {
        target: process.env.KITSU_API_TARGET || 'http://localhost:5000',
        changeOrigin: true,
        pathRewrite: {
          '^/api': ''
        }
      }
    }
  },
  chainWebpack: config => {
    config.module
      .rule('glsl')
      .test(/\.glsl$/)
      .use('webpack-glsl-loader')
        .loader('webpack-glsl-loader')
        .end()
  }
}

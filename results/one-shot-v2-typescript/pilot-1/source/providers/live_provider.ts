import emitter from '@adonisjs/core/services/emitter'
import server from '@adonisjs/core/services/server'
import { attachLive } from '../app/domain/live.js'

export default class LiveProvider {
  async ready() {
    emitter.on('http:server_ready', () => {
      const nodeServer = server.getNodeServer()
      if (nodeServer) attachLive(nodeServer)
    })
  }
}

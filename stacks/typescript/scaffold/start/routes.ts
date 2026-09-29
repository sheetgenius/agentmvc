import router from '@adonisjs/core/services/router'

router.get('/health', () => ({ status: 'ok' }))

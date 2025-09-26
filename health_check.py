import asyncio
import logging
from aiohttp import web
from aiohttp.web import Request, Response

logger = logging.getLogger(__name__)

class HealthCheckServer:
    def __init__(self, port: int = 8000):
        self.port = port
        self.app = web.Application()
        self.runner = None
        self.site = None

        # Setup routes
        self.app.router.add_get('/health', self.health_check)
        self.app.router.add_get('/', self.root_handler)

    async def health_check(self, request: Request) -> Response:
        """Health check endpoint for Koyeb"""
        return web.json_response({
            'status': 'healthy',
            'service': 'mirror-leech-bot',
            'version': '1.0.0'
        })

    async def root_handler(self, request: Request) -> Response:
        """Root endpoint"""
        return web.Response(
            text="🤖 Mirror Leech Bot is running!",
            content_type="text/plain"
        )

    async def start(self):
        """Start the health check server"""
        try:
            self.runner = web.AppRunner(self.app)
            await self.runner.setup()

            self.site = web.TCPSite(self.runner, '0.0.0.0', self.port)
            await self.site.start()

            logger.info(f"✅ Health check server started on port {self.port}")

        except Exception as e:
            logger.error(f"❌ Failed to start health check server: {e}")
            raise

    async def stop(self):
        """Stop the health check server"""
        try:
            if self.site:
                await self.site.stop()

            if self.runner:
                await self.runner.cleanup()

            logger.info("✅ Health check server stopped")

        except Exception as e:
            logger.error(f"Error stopping health check server: {e}")

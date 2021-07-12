from aiohttp import web
from statefun import *


functions = StatefulFunctions()


#
# Serve the functions
#
def run():
    handler = RequestReplyHandler(functions)


    async def handle(request):
        req = await request.read()
        res = await handler.handle_async(req)
        return web.Response(body=res, content_type="application/octet-stream")


    app = web.Application()
    app.add_routes([web.post('/statefun', handle)])

    web.run_app(app, port=8001)
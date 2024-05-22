import asyncio
from aiohttp import web

import argparse


class CustomQueue:
    def __init__(self):
        self.queue = asyncio.Queue()
        self.lock = asyncio.Lock()

    async def put(self, result):
        await self.queue.put(result)

    async def get(self, timeout=None):
        if self.queue.empty() and timeout is None:
            return None
        try:
            async with self.lock:
                result = await asyncio.wait_for(self.queue.get(), timeout)
            return result
        except asyncio.TimeoutError:
            return None

def is_prime(n):
    if n <= 1:
        return False
    if n <= 3:
        return True
    if n % 2 == 0 or n % 3 == 0:
        return False
    i = 5
    while i * i <= n: # up to sqrt
        if n % i == 0 or n % (i + 2) == 0:
            return False
        i += 6 # 2*3 primes
    return True

def sum_primes(v):  # synchronized
    return sum(1 for x in range(2, v + 1) if is_prime(x))

async def put_handler(request):
    v = request.query.get('v')
    if v is None:
        return web.Response(status=400)
    v = int(v)
    asyncio.create_task(count_and_put(v))
    return web.Response(status=200)

async def get_handler(request):
    timeout = request.query.get('timeout')
    if timeout is not None:
        timeout = int(timeout)
    result = await result_queue.get(timeout=timeout)
    if result is None:
        return web.Response(status=404)
    return web.json_response(result)

async def count_and_put(v):
    count = await asyncio.to_thread(sum_primes, v)   # to free loop, slows a bit due to GIL
    result = {'v': v, 'count': count}
    await result_queue.put(result)

def create_app():
    app = web.Application()
    app.add_routes([web.put('/number', put_handler), web.get('/number', get_handler)])
    return app

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=5000, help='1000 < port # < 65M')
    args = parser.parse_args()

    result_queue = CustomQueue()
    app = create_app()
    web.run_app(app, port=args.port)

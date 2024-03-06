from src.common.web_handler import WebHandler, url_unescape
from .views import *


class EnvHandler(WebHandler):
    async def get(self, *args, **kwargs):
        query = self.get_request_query_json()
        env = Env()
        data = await env.list_env(**query)
        self.reply(**data)

    async def post(self, *args, **kwargs):
        body = self.get_request_body_json()
        env = Env()
        body['user'] = self.current_user
        await env.add(**body)
        self.reply()

    async def put(self, *args, **kwargs):
        body = self.get_request_body_json()
        env = Env()
        body['user'] = self.current_user
        await env.update(**body)
        self.reply()

    async def delete(self, *args, **kwargs):
        body = self.get_request_body_json()
        env = Env()
        await env.delete(**body)
        self.reply()

env_urls = [
    (r'/env', EnvHandler),
]

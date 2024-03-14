from src.common.web_handler import WebHandler
from .views import *


class CallbackHandler(WebHandler):

    # def prepare(self):
    #     pass
    # async def get(self, *args, **kwargs):
    #     query = self.get_request_query_json()
    #     env = Env()
    #     data = await env.list_env(**query)
    #     self.reply(**data)

    async def post(self, *args, **kwargs):
        body = self.get_request_body_json()
        cb = Callback()
        # body['user'] = self.current_user
        data = await cb.general_callback(**body)
        self.reply(**data)

    # async def put(self, *args, **kwargs):
    #     body = self.get_request_body_json()
    #     env = Env()
    #     body['user'] = self.current_user
    #     await env.update(**body)
    #     self.reply()
    #
    # async def delete(self, *args, **kwargs):
    #     body = self.get_request_body_json()
    #     env = Env()
    #     await env.delete(**body)
    #     self.reply()


class TempHandler(WebHandler):

    async def post(self, *args, **kwargs):
        from src.common.log_handler import logger
        body = self.get_request_body_json()
        # print('!!!!!!!!!!!!!!', body)
        # body['user'] = self.current_user
        # await env.add(**body)
        self.reply()

callback_urls = [
    (r'/callback', CallbackHandler),
    (r'/temp', TempHandler),
]

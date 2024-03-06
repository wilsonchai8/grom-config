from src.common.web_handler import WebHandler, url_unescape
from .views import *


class PublicHandler(WebHandler):
    async def get(self, *args, **kwargs):
        query = self.get_request_query_json()
        pi = PublicItem()
        data = await pi.list_public_item(**query)
        self.reply(**data)

    async def post(self, *args, **kwargs):
        body = self.get_request_body_json()
        body['user'] = self.current_user
        pi = PublicItem()
        await pi.add(**body)
        self.reply()

    async def put(self, *args, **kwargs):
        body = self.get_request_body_json()
        body['user'] = self.current_user
        pi = PublicItem()
        await pi.update(**body)
        self.reply()

    async def delete(self, *args, **kwargs):
        body = self.get_request_body_json()
        body['user'] = self.current_user
        pi = PublicItem()
        await pi.delete(**body)
        self.reply()


class PublicVersionHandler(WebHandler):
    async def get(self, *args, **kwargs):
        query = self.get_request_query_json()
        pi = PublicItem()
        data = await pi.list_public_item_version(**query)
        self.reply(**data)


class PublicPublishHandler(WebHandler):
    async def post(self, *args, **kwargs):
        body = self.get_request_body_json()
        body['user'] = self.current_user
        pi = PublicItem()
        await pi.publish(**body)
        self.reply()


class PublicRollbackHandler(WebHandler):
    async def post(self, *args, **kwargs):
        body = self.get_request_body_json()
        body['user'] = self.current_user
        pi = PublicItem()
        await pi.rollback(**body)
        self.reply()


class PublicRelatedGeneralHandler(WebHandler):
    async def get(self, *args, **kwargs):
        query = self.get_request_query_json()
        pi = PublicItem()
        data = await pi.related_general(**query)
        self.reply(**data)

    async def post(self, *args, **kwargs):
        body = self.get_request_body_json()
        body['user'] = self.current_user
        pi = PublicItem()
        await pi.related_general_publish(**body)
        self.reply()


public_urls = [
    (r'/public', PublicHandler),
    (r'/public/publish', PublicPublishHandler),
    (r'/public/rollback', PublicRollbackHandler),
    (r'/publicversion', PublicVersionHandler),
    (r'/public/related_general', PublicRelatedGeneralHandler),
]

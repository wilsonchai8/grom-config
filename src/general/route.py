from src.common.web_handler import WebHandler, url_unescape
from .views import *

    
class GeneralHandler(WebHandler):
    async def get(self, *args, **kwargs):
        query = self.get_request_query_json()
        general = General()
        data = await general.list_general(**query)
        self.reply(**data)

    async def post(self, *args, **kwargs):
        body = self.get_request_body_json()
        general = General()
        body['user'] = self.current_user
        await general.add(**body)
        self.reply()

    async def put(self, *args, **kwargs):
        body = self.get_request_body_json()
        body['user'] = self.current_user
        general = General()
        await general.update(**body)
        self.reply()

    async def delete(self, *args, **kwargs):
        body = self.get_request_body_json()
        body['user'] = self.current_user
        general = General()
        await general.general_permission(**body)
        self.reply()


class GeneralRenderHandler(WebHandler):
    async def post(self, *args, **kwargs):
        body = self.get_request_body_json()
        body['user'] = self.current_user
        general = General()
        data = await general.render(**body)
        self.reply(**data)


class GeneralVersionHandler(WebHandler):
    async def get(self, *args, **kwargs):
        query = self.get_request_query_json()
        general = General()
        data = await general.list_general_version(**query)
        self.reply(**data)

    async def post(self, *args, **kwargs):
        body = self.get_request_body_json()
        general = General()
        data = await general.fuzzysearch_general_version(**body)
        self.reply(**data)


class GeneralVersionLogPublishHandler(WebHandler):
    async def get(self, *args, **kwargs):
        query = self.get_request_query_json()
        general = General()
        data = await general.list_general_version_log(**query)
        self.reply(**data)


class GeneralStatusHandler(WebHandler):
    async def get(self, *args, **kwargs):
        query = self.get_request_query_json()
        general = General()
        data = await general.general_status(**query)
        self.reply(**data)


class GeneralPublishHandler(WebHandler):
    async def post(self, *args, **kwargs):
        body = self.get_request_body_json()
        body['user'] = self.current_user
        general = General()
        await general.publish(**body)
        self.reply()


class GeneralPublishStopHandler(WebHandler):
    async def post(self, *args, **kwargs):
        body = self.get_request_body_json()
        body['user'] = self.current_user
        general = General()
        await general.publish_stop(**body)
        self.reply()


class GeneralAbandonHandler(WebHandler):
    async def post(self, *args, **kwargs):
        body = self.get_request_body_json()
        body['user'] = self.current_user
        general = General()
        await general.abandon(**body)
        self.reply()


class GeneralRollbackHandler(WebHandler):
    async def post(self, *args, **kwargs):
        body = self.get_request_body_json()
        body['user'] = self.current_user
        general = General()
        await general.rollback(**body)
        self.reply()


class GeneralRollbackStopHandler(WebHandler):
    async def post(self, *args, **kwargs):
        body = self.get_request_body_json()
        body['user'] = self.current_user
        general = General()
        await general.rollback_stop(**body)
        self.reply()


general_urls = [
    (r'/general', GeneralHandler),
    (r'/general/status', GeneralStatusHandler),
    (r'/general/render', GeneralRenderHandler),
    (r'/general/abandon', GeneralAbandonHandler),
    (r'/general/publish', GeneralPublishHandler),
    (r'/general/publishstop', GeneralPublishStopHandler),
    (r'/general/rollback', GeneralRollbackHandler),
    (r'/general/rollbackstop', GeneralRollbackStopHandler),
    (r'/generalversion', GeneralVersionHandler),
    (r'/generallog', GeneralVersionLogPublishHandler),
]

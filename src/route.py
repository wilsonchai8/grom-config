from .common.web_handler import WebHandler, HTTPError
from .general.route import general_urls
from .public.route import public_urls
from .callback.route import callback_urls
from .env.route import env_urls


class HelloHandler(WebHandler):

    async def get(self, *args, **kwargs):
        print('hello world')
        self.reply(msg='hello world!')

    def prepare(self):
        pass


class NotFoundHandler(WebHandler):
    async def prepare(self):
        raise HTTPError(status_code=404, log_message=self.request.uri)


urls = []

for item in [general_urls, public_urls, callback_urls, env_urls]:
    urls.extend(item)

urls.extend(
    [
        (r'/hello', HelloHandler),
        (r'/.*', NotFoundHandler),
    ]
)

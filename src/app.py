from .common.config import get_conf
from .common.web_handler import *
from .route import urls
from .asy.mysql_client import MysqlPool
import asyncio
import pymysql
from .mq_init import SQL


class MysqlInitial:
    def __init__(self, mq):
        self.mq = mq

    def run(self):
        try:
            conn = self.conn_mysql(**self.mq)
            with conn:
                cur = conn.cursor()
                cur.execute('show tables')
        except Exception as e:
            logger.error(e)
            err_code, _ = e.args
            if err_code == 1049:
                conn = self.conn_mysql(database=False, **self.mq)
                with conn:
                    cur = conn.cursor()
                    for sql in SQL:
                        cur.execute(sql)
            else:
                raise e

    def conn_mysql(self, database=True, **kwargs):
        db = kwargs['db'] if database else ''
        return pymysql.connect(
            host=kwargs['host'],
            port=int(kwargs['port']),
            user=kwargs['user'],
            password=kwargs['password'],
            db=db
        )


def _init():
    mysql_configs = get_conf().get('mysql', {})
    MysqlInitial(mysql_configs).run()
    loop = get_loop()
    mp = MysqlPool(loop)
    asyncio.run_coroutine_threadsafe(mp.create_mysql_pool(), loop)


def main():
    settings = get_conf().get('tornado', {})
    app = Application(urls, **settings)
    server = httpserver.HTTPServer(app)
    server.bind(10002, '0.0.0.0')
    server.start(1)
    _init()
    IOLoop.current().start()

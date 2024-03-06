from src.common.utils import Singleton
from src.common.exception_handler import MysqlError
from src.common.config import get_conf
import aiomysql
import asyncio
from threading import Lock

lock = Lock()


class MysqlPool(metaclass=Singleton):
    def __init__(self, loop):
        self.loop = loop
        self.pool = None
        self.retry = 3
        self.interval = 1
        self.mq = get_conf()['mysql']

    def __new__(cls, *args, **kwargs):
        return super().__new__(cls)

    async def create_mysql_pool(self):
        if lock.acquire(blocking=False):
            self.pool = await aiomysql.create_pool(
                host=self.mq['host'],
                port=int(self.mq['port']),
                user=self.mq['user'],
                password=self.mq['password'],
                db=self.mq['db'],
                loop=self.loop,
                # autocommit=True
            )
            lock.release()

    async def check_pool(self):
        try:
            retry = 0
            while not self.pool and retry < self.retry:
                await asyncio.sleep(self.interval)
                retry += 1
            if retry == self.retry:
                raise MysqlError('can not establish connection...')
        except Exception as e:
            print(e)
            _, code = e.args
            if code == 3:
                await self.create_mysql_pool()
            raise(e)

    async def dml(self, sql, conditions=(), all=False):
        ret = None
        async with self.pool.acquire() as conn:
            cur = await conn.cursor(aiomysql.cursors.DictCursor) 
            try:
                await cur.execute(sql, conditions)
                await conn.commit()
            except Exception as e:
                await conn.rollback()
                raise(e)
            ret = await cur.fetchone() if not all else await cur.fetchall()
        return ret

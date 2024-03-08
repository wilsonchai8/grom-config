from src.asy.mysql_client import MysqlPool
from src.common.web_handler import get_loop
from src.common.exception_handler import *
from src.common.meta import *
from datetime import datetime

__all__ = (
    'Env',
)


class EnvAdd(ConfigMetaClass):
    name = NonBlank('name')
    prefix = MustString('prefix')
    comment = MustString('comment')
    notification = MustString('notification')
    notification_token = MustString('notification_token')
    callback_token = MustString('callback_token')
    is_callback = MaybeBool('is_callback')
    
    def __init__(self, *args, **kwargs) -> None:
        self.name = kwargs.get('name')
        self.prefix = kwargs.get('prefix')
        self.comment = kwargs.get('comment')
        self.notification = kwargs.get('notification')
        self.notification_token = kwargs.get('notification_token')
        self.callback_token = kwargs.get('callback_token')
        self.is_callback = kwargs.get('is_callback')
        
        super().__init__(*args, **kwargs)


class EnvInfo(ConfigMetaClass):
    id = MustInteger('id')
    
    def __init__(self, *args, **kwargs) -> None:
        self.id = kwargs.get('id')
        
        super().__init__(*args, **kwargs)


class EnvUpdate(EnvAdd):
    id = MustInteger('id')
    
    def __init__(self, *args, **kwargs) -> None:
        self.id = kwargs.get('id')
        
        super().__init__(*args, **kwargs)


class EnvDelete(EnvInfo): pass


class Env:

    def __init__(self) -> None:
        self.loop = get_loop()
        self.mp = MysqlPool(self.loop)

    async def add(self, **kwargs):
        ea = EnvAdd(**kwargs)
        await EnvCheck.env_found(ea.name, ea.prefix)

        user = kwargs.get('user')
        now = datetime.now()

        add_env_sql = "insert into env(name, prefix, comment, notification, notification_token, is_callback, callback_token, update_time, modifier)" \
                    "values(%s, %s, %s, %s, %s, %s, %s, %s, %s)"
        add_env_condition = (ea.name, ea.prefix, ea.comment, ea.notification, ea.notification_token, 
                             ea.is_callback, ea.callback_token, now, user)
        await self.mp.dml(add_env_sql, add_env_condition)

    async def list_env(self, id=None, page=1, limit=15, **kwargs):
        ret = {
            'env_counts': 0,
            'env_list': [],
            'env_info': {}
        }
        if id:
            ei = EnvInfo(id=id)
            sql = "select * from env where id = %s"
            condition = (ei.id,)
            ret['env_info'] = await self.mp.dml(sql, condition)
        else:
            counts_sql = "select count(1) as counts from env "
            counts_res = await self.mp.dml(counts_sql)
            page = int(page) - 1 if int(page) > 1 else 0
            limit = int(limit)
            env_list_sql = "select * from env " \
                "order by id desc limit {},{} ".format(page*limit, limit)
            env_list_ret = await self.mp.dml(env_list_sql, all=True)
            ret['env_counts'] = counts_res['counts']
            ret['env_list'] = env_list_ret
        return ret

    async def update(self, **kwargs):
        eu = EnvUpdate(**kwargs)
        await EnvCheck.env_not_found(eu.id)

        user = kwargs.get('user')
        now = datetime.now()

        sql = "update env set name=%s, prefix=%s, comment=%s, notification=%s, notification_token=%s, is_callback=%s, " \
                "callback_token=%s, update_time=%s, modifier=%s where id=%s"
        condition = (eu.name, eu.prefix, eu.comment, eu.notification, eu.notification_token, 
                     eu.is_callback, eu.callback_token, now, user, eu.id)
        await self.mp.dml(sql, condition)

    async def delete(self, **kwargs):
        ed = EnvDelete(**kwargs)
        await EnvCheck.env_not_found(ed.id)
        await EnvCheck.env_can_not_delete(ed.id)

        sql = "delete from env where id = %s"
        condition = (ed.id,)
        await self.mp.dml(sql, condition)


class EnvCheck:

    @classmethod
    async def env_found(cls, name, prefix, **kwargs):
        mp = MysqlPool(get_loop())
        sql = "select count(1) as count from env " \
            "where name=%s and prefix=%s"
        cond = (name, prefix)
        query = await mp.dml(sql, conditions=cond)
        if query.get('count') == 1:
            raise RunError(msg='环境已存在')

    @classmethod
    async def env_not_found(cls, id, **kwargs):
        mp = MysqlPool(get_loop())
        sql = "select count(1) as count from env " \
            "where id=%s"
        cond = (id,)
        query = await mp.dml(sql, conditions=cond)
        if query.get('count') == 0:
            raise RunError(msg='找不到对应的环境，请刷新')

    @classmethod
    async def env_can_not_delete(cls, id, **kwargs):
        mp = MysqlPool(get_loop())
        sql = "select count(1) as count from general " \
            "where env_id=%s"
        cond = (id,)
        query = await mp.dml(sql, conditions=cond)
        if query.get('count') > 0:
            raise RunError(msg='环境被配置文件引用，不能删除')

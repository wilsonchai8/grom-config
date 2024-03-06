from src.asy.mysql_client import MysqlPool
from src.common.web_handler import get_loop
from src.common.exception_handler import *

class GeneralCheck:
    
    @classmethod
    async def general_found(cls, name, env_id, belongto, **kwargs):
        mp = MysqlPool(get_loop())
        sql = "select count(1) as count from general " \
            "where name=%s and env_id=%s and belongto=%s "
        cond = (name, env_id, belongto)
        query = await mp.dml(sql, conditions=cond)
        if query.get('count') == 1:
            raise RunError(msg='配置文件已存在')

    @classmethod
    async def general_not_found(cls, general_id, **kwargs):
        mp = MysqlPool(get_loop())
        sql = "select count(1) as count from general " \
            "where id=%s and is_delete=0"
        cond = (general_id,)
        query = await mp.dml(sql, conditions=cond)
        if query.get('count') == 0:
            raise RunError(msg='配置文件找不到')

    @classmethod
    async def rollback_forbidden(cls, general_id, **kwargs):
        mp = MysqlPool(get_loop())
        sql = "select count(1) as count from general_version " \
            "where general_id=%s and status='modified'"
        cond = (general_id,)
        query = await mp.dml(sql, conditions=cond)
        if query.get('count') > 0:
            raise RunError(msg='有未发布的版本，不能回滚')

    @classmethod
    async def being_publishing_or_rollbacking(cls, general_id, **kwargs):
        detail = kwargs['detail']
        mp = MysqlPool(get_loop())
        sql = "select count(1) as count from general_version " \
            "where general_id=%s and status in ('publishing', 'rollbacking')"
        cond = (general_id,)
        query = await mp.dml(sql, conditions=cond)
        if query.get('count') > 0:
            msg = '有版本正在发布/回滚中，不能{}'.format(detail)
            raise RunError(msg=msg)


    @classmethod
    async def abandon_forbidden(cls, general_id, version_id, **kwargs):
        mp = MysqlPool(get_loop())
        sql = "select count(1) as count from general_version where general_id = %s"
        cond = (general_id,)
        query = await mp.dml(sql, conditions=cond)
        if query.get('count') == 1:
            raise RunError(msg='该配置文件从未发布过，当前版本不能放弃')
        sql = "select count(1) as count from general_version where id=%s and status<>'modified'"
        cond = (version_id,)
        query = await mp.dml(sql, conditions=cond)
        if query.get('count') > 0:
            raise RunError(msg='当前版本已发布，不能被放弃')


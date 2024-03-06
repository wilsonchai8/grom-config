from src.asy.mysql_client import MysqlPool
from src.common.web_handler import get_loop
from src.common.exception_handler import *
from src.common.log_handler import logger
from src.common.state_machine import states_to_name
from src.general.internal import publish_flow
from .meta import *
from datetime import datetime
import asyncio
import traceback


__all__ = (
    'PublicItem',
)


class PublicItem:

    def __init__(self) -> None:
        self.loop = get_loop()
        self.mp = MysqlPool(self.loop)

    async def add(self, public_item_id=None, **kwargs):
        pa = PublicItemAdd(**kwargs)
        user = kwargs.get('user')
        now = datetime.now()

        async with self.mp.pool.acquire() as conn:
            cur = await conn.cursor() 
            try:
                if not public_item_id:
                    await PublicItemCheck.public_item_found(pa.key, pa.env_id)

                    await cur.execute(
                        "insert into public_item(env_id, k, create_time, creator) values (%s ,%s ,%s ,%s)",
                        (pa.env_id, pa.key, now, user)
                    )

                    public_item_id = cur.lastrowid
                version = datetime.strftime(now, '%Y%m%d-%H%M%S')
                await cur.execute(
                    "insert into public_item_version(public_item_id, name, v, status, update_time, modifier) " \
                        "values (%s, %s, %s, %s, %s, %s)",
                    (public_item_id, version, pa.value, 'modified', now, user)
                )
                await conn.commit()
            except Exception as e:
                await conn.rollback()
                raise(e)

    async def update(self, **kwargs):
        pvu = PublicItemVersionUpdate(**kwargs)
        await PublicItemCheck.public_item_not_found(pvu.public_item_id)
        user = kwargs.get('user')
        now = datetime.now()

        current_version_info = await self.mp.dml(
            "select * from public_item_version where public_item_id = %s and status = 'modified' order by update_time desc limit 1 ",
            (pvu.public_item_id,)
        )
        if current_version_info:
            if current_version_info['id'] != pvu.version_id:
                msg = '{} 版本正在更新，无法更新当前版本'.format(current_version_info['name'])
                raise RunError(msg=msg)
            update_version_sql = "update public_item_version set v = %s, update_time = %s, modifier = %s " \
                                "where id = %s and status = 'modified'"
            update_version_condition = (pvu.value, now, user, current_version_info['id'])
            await self.mp.dml(update_version_sql, update_version_condition)
        else:
            await self.add(public_item_id=pvu.public_item_id, **kwargs)

    async def publish(self, **kwargs):
        pp = PublicItemPublish(**kwargs)
        now = datetime.now()
        user = kwargs['user']
        await PublicItemCheck.public_item_not_found(pp.public_item_id)

        publish_sql = "update public_item_version set status = %s, publisher = %s, publish_time = %s " \
                    "where id = %s and status = 'modified'"
        publish_condition = ('published', user, now, pp.version_id )
        await self.mp.dml(publish_sql, publish_condition)
        # await self.update_public_item_version_record(version_id=pp.version_id)

    async def rollback(self, **kwargs):
        pr = PublicItemRollback(**kwargs)
        await PublicItemCheck.public_item_not_found(pr.public_item_id)
        await PublicItemCheck.rollback_forbidden(pr.public_item_id)

        now = datetime.now()
        user = kwargs['user']

        rollback_sql = "update public_item_version set publisher = %s, publish_time = %s, modifier = %s, update_time = %s " \
                    "where id = %s"
        rollback_condition = (user, now, user, now, pr.version_id)
        await self.mp.dml(rollback_sql, rollback_condition)

    async def list_public_item(self, id=None, page=1, limit=20, k='', env='', prefix='', **kwargs):
        ret = {
            'public_item_counts': 0,
            'public_item_list': [],
            'public_item_info': {}
        }
        if id:
            sql = "select a.id, a.k, b.v, b.name as version, b.status, b.publish_time, b.publisher, b.update_time, b.modifier, " \
                "c.name as env, c.prefix " \
                "from public_item a, public_item_version b, env c " \
                "where a.id = b.public_item_id and a.env_id = c.id " \
                "and b.public_item_id = %s"
            ret['public_item_info'] = await self.mp.dml(
                sql,
                (id,)
            )
        else:
            page = int(page) - 1 if int(page) > 1 else 0
            limit = int(limit)
            cond = (env, prefix, k,)

            counts_sql = "select count(1) as counts from " \
                "(select * from env " \
                "where name like CONCAT('%%', %s, '%%') " \
                "and prefix like CONCAT('%%', %s, '%%')) e," \
                "(select * from public_item " \
                "where k like CONCAT('%%', %s, '%%') " \
                ") p where p.env_id = e.id"
            counts_res = await self.mp.dml(counts_sql, cond)

            public_item_list_sql = "select p.*, e.name as env, e.prefix from " \
                "(select * from env " \
                "where name like CONCAT('%%', %s, '%%') " \
                "and prefix like CONCAT('%%', %s, '%%')) e," \
                "(select * from public_item " \
                "where k like CONCAT('%%', %s, '%%') " \
                ") p where p.env_id = e.id order by id desc limit {},{}".format(page*limit, limit)
            public_item_list_ret = await self.mp.dml(public_item_list_sql, cond, all=True)
            ret['public_item_counts'] = counts_res['counts']
            ret['public_item_list'] = public_item_list_ret

        return ret

    async def list_public_item_version(self, **kwargs):
        ret = {
            'public_item_version_list': []
        }
        pv = PublicItemVersionInfo(**kwargs)
        await PublicItemCheck.public_item_not_found(pv.public_item_id)

        sql = "select * from public_item_version where public_item_id = %s order by update_time desc" 
        condition = (pv.public_item_id,)
        ret['public_item_version_list'] = await self.mp.dml(sql, condition, all=True)

        return ret

    async def delete(self, **kwargs):
        pd = PublicItemDelete(**kwargs)

        for public_item_id in pd.public_item_ids:
            public_item_sql = "select p.*, e.name env, e.prefix from public_item p, env e " \
                "where p.env_id = e.id and p.id = %s"
            public_item_condition = (public_item_id,)
            public_item_condition_info = await self.mp.dml(public_item_sql, public_item_condition)

            quote_sql = "select count(1) counts from general_version where content like CONCAT('%%', '<<<', %s, '>>>', '%%')"
            quote_string = '{}.{}.{}'.format(public_item_condition_info['env'], public_item_condition_info['prefix'], public_item_condition_info['k'])
            quote_condition = (quote_string,)
            quote_res = await self.mp.dml(quote_sql, quote_condition)
            if quote_res['counts'] > 0:
                raise RunError(msg='该公共配置被引用，不能删除')

        async with self.mp.pool.acquire() as conn:
            cur = await conn.cursor() 
            try:
                await cur.execute(
                    "delete from public_item where id in %s",
                    (pd.public_item_ids,)
                )
                await cur.execute(
                    "delete from public_item_version where public_item_id in %s",
                    (pd.public_item_ids,)
                )
                await conn.commit()
            except Exception as e:
                await conn.rollback()
                raise(e)

    async def related_general(self, **kwargs):
        ret = {
            'related_general': list()
        }
        payload = list()
        pvr = PublicItemVersionRecord(**kwargs)
        related_sql = "select * from (select t1.* from " \
            "(select g.name, g.belongto, gv.id version_id, gv.general_id, gv.name version, gv.content, gv.status, gv.publish_time, gv.update_time, e.name env, e.prefix " \
            "from general g, general_version gv, env e " \
            "where g.id = gv.general_id and e.id = g.env_id) t1 " \
            "left join (select general_id, max(update_time) update_time from general_version group by general_id) t2 " \
            "on t1.general_id = t2.general_id and t1.update_time < t2.update_time " \
            "where t1.content like CONCAT('%%', %s, '%%') and t2.general_id is null) a " \
            "left join (select general_version_id, msg, update_time as related_general_update_time, modifier as related_general_modifier " \
            "from public_item_version_record where public_item_version_id = %s) b on a.version_id = b.general_version_id"
        related_general_info = await self.mp.dml(
            related_sql,
            (pvr.k, pvr.public_item_version_id),
            all=True
        )
        for piece in related_general_info:
            is_publish = False
            payload.append(
                {
                    'name': piece['name'],
                    'env': piece['env'],
                    'prefix': piece['prefix'],
                    'belongto': piece['belongto'],
                    'general_id': piece['general_id'],
                    'version_id': piece['version_id'],
                    'version': piece['version'],
                    'content': piece['content'],
                    'status': piece['status'],
                    'publish_time': piece['publish_time'],
                    'is_publish': is_publish,
                    'general_version_id': piece['general_version_id'],
                    'msg': piece['msg'],
                    'related_general_update_time': piece['related_general_update_time'],
                    'related_general_modifier': piece['related_general_modifier'],
                }
            )
        ret['related_general'] = payload
        return ret

    async def _publish(self, ob_list, public_item_version_id, user):

        async def _writeback(general_version_id, error_message=None):
            res = await self.mp.dml(
                "select count(1) count from public_item_version_record " \
                "where public_item_version_id = %s and general_version_id = %s",
                (public_item_version_id, general_version_id)
            )
            now = datetime.now()
            if res['count'] > 0:
                sql = "update public_item_version_record set msg = %s, update_time = %s, modifier = %s " \
                    "where public_item_version_id = %s and general_version_id = %s"
                conditions = (error_message, now, user, public_item_version_id, general_version_id)
            else:
                sql = "insert into public_item_version_record(public_item_version_id, general_version_id, msg, update_time, modifier) " \
                    "values(%s, %s, %s, %s, %s)"
                conditions = (public_item_version_id, general_version_id, error_message, now, user)
            await self.mp.dml(sql, conditions)

        for ob in ob_list:
            payload = {
                'user': user
            }
            payload.update(ob)
            try:
                error_message = None
                await publish_flow(**payload)
            except Exception as e:
                error_message = e

            try:
                await _writeback(
                    ob['version_idaaa'],
                    error_message
                )
            except Exception:
                logger.error(traceback.format_exc())

    async def related_general_publish(self, **kwargs):
        user = kwargs.get('user')
        pvrgp = PublicItemVersionRelatedGeneralPublish(**kwargs)
        await PublicItemCheck.public_item_version_is_modified(pvrgp.public_item_version_id)
        asyncio.run_coroutine_threadsafe(self._publish(pvrgp.related_general_list, pvrgp.public_item_version_id, user), self.loop)

class PublicItemCheck:

    @classmethod
    async def public_item_found(cls, k, env_id, **kwargs):
        mp = MysqlPool(get_loop())
        query = await mp.dml(
            "select count(1) as count from public_item where k=%s and env_id=%s ",
            (k, env_id, )
        )
        if query.get('count') == 1:
            raise RunError(msg='公共配置已存在')

    @classmethod
    async def public_item_not_found(cls, public_item_id, **kwargs):
        mp = MysqlPool(get_loop())
        query = await mp.dml(
            "select count(1) as count from public_item where id=%s",
            (public_item_id,)
        )
        if query.get('count') == 0:
            raise RunError(msg='公共配置找不到')

    @classmethod
    async def rollback_forbidden(cls, public_item_id, **kwargs):
        mp = MysqlPool(get_loop())
        query = await mp.dml(
            "select count(1) as count from public_item_version where public_item_id=%s and status='modified'",
            (public_item_id,)
        )
        if query.get('count') > 0:
            raise RunError(msg='有未发布的版本，不能回滚')

    @classmethod
    async def public_item_version_is_modified(cls, public_item_version_id, **kwargs):
        mp = MysqlPool(get_loop())
        query = await mp.dml(
            "select count(1) as count from public_item_version where id=%s and status='modified'",
            (public_item_version_id,)
        )
        if query.get('count') > 0:
            raise RunError(msg='当前公共配置未发布，不能发布关联配置')

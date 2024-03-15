from src.asy.mysql_client import MysqlPool
from src.common.web_handler import get_loop
from .check import *
from .meta import *
from .internal import *
from datetime import datetime


__all__ = (
    'General',
)


class General:

    def __init__(self) -> None:
        self.loop = get_loop()
        self.mp = MysqlPool(self.loop)

    async def general_status(self, **kwargs):
        return {
            'general_status': states_to_name
        }

    async def add(self, id=None, **kwargs):
        ga = GeneralAdd(**kwargs)
        user = kwargs.get('user')
        now = datetime.now()

        async with self.mp.pool.acquire() as conn:
            cur = await conn.cursor() 
            cs = ConfigStatus('modified')
            try:
                if not id:
                    await GeneralCheck.general_found(**kwargs)
                    general_sql = "insert into general(name, env_id, belongto, create_time, creator) " \
                        "values (%s, %s, %s, %s, %s)"
                    general_condition = (ga.name, ga.env_id, ga.belongto, now, user)
                    await cur.execute(general_sql, general_condition)
                    id = cur.lastrowid
                general_version_name = datetime.strftime(now, '%Y%m%d-%H%M%S')
                general_version_sql = "insert into general_version(general_id, name, content, status, update_time, modifier) " \
                        "values (%s, %s, %s, %s, %s, %s)"
                general_version_condition = (id, general_version_name, ga.content, cs.state, now, user)
                await cur.execute(general_version_sql, general_version_condition)
                version_id = cur.lastrowid
                await conn.commit()
            except Exception as e:
                await conn.rollback()
                raise(e)

            await add_general_version_log(
                general_id=id,
                version_id=version_id,
                name='{} 编辑成功'.format(general_version_name),
                status=cs.state,
                info=ga.content,
                user=user,
                update_time=now
            )

    async def update(self, id, **kwargs):
        gvu = GeneralVersionUpdate(general_id=id, **kwargs)
        await GeneralCheck.general_not_found(general_id=gvu.general_id)
        await GeneralCheck.being_publishing_or_rollbacking(general_id=gvu.general_id, detail='修改')
        user = kwargs.get('user')
        now = datetime.now()
        
        current_version_sql = "select * from general_version where general_id = %s and status = 'modified' order by update_time desc limit 1 "
        current_version_condition = (gvu.general_id,)
        current_version_info = await self.mp.dml(current_version_sql, current_version_condition)
        cs = ConfigStatus('modified')
        if current_version_info:
            if current_version_info['id'] != gvu.version_id:
                msg = '{} 版本正在更新，无法更新当前版本'.format(current_version_info['name'])
                raise RunError(msg=msg)
            update_version_sql = "update general_version set content = %s, update_time = %s, modifier = %s " \
                                "where id = %s and status = 'modified'"
            update_version_condition = (gvu.content, now, user, current_version_info['id'])
            await self.mp.dml(update_version_sql, update_version_condition)
            await add_general_version_log(
                general_id=id,
                version_id=current_version_info['id'],
                name='{} 编辑成功'.format(current_version_info['name']),
                status=cs.state,
                info=gvu.content,
                user=user,
                update_time=now
            )
        else:
            await self.add(id=id, **kwargs)

    async def list_general(self, id=None, page=1, limit=20, isDelete='0', name='', belongto='', env='', prefix='', **kwargs):
        ret = {
            'general_counts': 0,
            'general_list': [],
            'general_info': {}
        }
        is_delete = isDelete.split(',')
        if id:
            gd = GeneralInfo(general_id=id)
            sql = "select a.id, a.name, a.belongto, " \
                "b.name as version, b.content, b.status, b.publish_time, b.publisher, b.update_time, b.modifier ," \
                "c.name as env, c.prefix" \
                "from general a, general_version b, env c" \
                "where a.env_id = c.id and a.id = b.general_id and a.is_delete in %s and a.id = %s;"
            condition = (is_delete, gd.general_id)
            ret['general_info'] = await self.mp.dml(sql, condition)
        else:
            page = int(page) - 1 if int(page) > 1 else 0
            limit = int(limit)
            cond = (env, prefix, name, belongto, is_delete)

            counts_sql = "select count(1) as counts from " \
                "(select * from env " \
                "where name like CONCAT('%%', %s, '%%') " \
                "and prefix like CONCAT('%%', %s, '%%')) e," \
                "(select * from general " \
                "where name like CONCAT('%%', %s, '%%') " \
                "and belongto like CONCAT('%%', %s, '%%') " \
                "and is_delete in %s) g where g.env_id = e.id"
            counts_res = await self.mp.dml(counts_sql, cond)
            general_list_sql = "select g.*, e.name as env, e.prefix, e.comment as comment from " \
                "(select * from env " \
                "where name like CONCAT('%%', %s, '%%') " \
                "and prefix like CONCAT('%%', %s, '%%')) e," \
                "(select * from general " \
                "where name like CONCAT('%%', %s, '%%') " \
                "and belongto like CONCAT('%%', %s, '%%') " \
                "and is_delete in %s) g where g.env_id = e.id order by id desc limit {},{}".format(page*limit, limit)
            general_list_ret = await self.mp.dml(general_list_sql, cond, all=True)
            ret['general_counts'] = counts_res['counts']
            ret['general_list'] = general_list_ret
        return ret

    async def general_permission(self, **kwargs):
        gp = GeneralPermission(**kwargs)
        general_ids = gp.general_ids
        
        general_info_res = await self.mp.dml(
            "select g.id, g.name, e.name env, g.belongto, e.prefix from general g, env e where g.env_id = e.id and g.id in %s",
            (general_ids, ),
            all=True
        )
        

        now = datetime.now()
        user = kwargs['user']
        is_delete = gp.is_delete
        permission = 'disabled' if is_delete else 'enabled'
        permission_string = states_to_name[permission]
        for general_info in general_info_res:
            update_general_sql = "update general set is_delete = %s where is_delete <> %s and id = %s " 
            update_general_condition = (is_delete, is_delete, general_info['id'])
            await self.mp.dml(update_general_sql, update_general_condition)

            info = 'id: {} -- name: {} -- env: {} -- belongto: {} -- prefix: {}，{}成功'\
                    .format(general_info['id'], general_info['name'], general_info['env'], general_info['belongto'], general_info['prefix'], permission_string)
            await add_general_version_log(
                general_id=general_info['id'],
                version_id=0,
                name='{} {} 成功'.format(general_info['name'], permission_string),
                status=permission,
                info=info,
                user=user,
                update_time=now
            )

    async def list_general_version(self, **kwargs):
        ret = {
            'general_version_list': [],
        }
        gvi = GeneralVersionInfo(**kwargs)
        await GeneralCheck.general_not_found(general_id=gvi.general_id)
        sql = "select * from general_version where general_id = %s order by update_time desc"
        condition = (gvi.general_id,)
        ret['general_version_list'] = await self.mp.dml(sql, condition, all=True)
        return ret

    async def abandon(self, **kwargs):
        gva = GeneralVersionAbandon(**kwargs)
        user = kwargs.get('user')
        await GeneralCheck.abandon_forbidden(general_id=gva.general_id, version_id=gva.version_id)
        now = datetime.now()

        current_version_info = await self.mp.dml(
            "select * from general_version where id = %s ",
            (gva.version_id,)
        )
        await self.mp.dml(
            "delete from general_version where id = %s and status = 'modified'",
            (gva.version_id,)
        )
        await add_general_version_log(
            general_id=gva.general_id,
            version_id=gva.version_id,
            status='abandon',
            name='{} 放弃修改'.format(current_version_info['name']),
            info='',
            user=user,
            update_time=now
        )

    async def publish(self, **kwargs):
        await publish_flow(**kwargs)

    async def publish_stop(self, **kwargs):
        gps = GeneralPublish(**kwargs)
        user = kwargs.get('user')
        now = datetime.now()
        await GeneralCheck.general_not_found(general_id=gps.general_id)


        to_publish_version_sql = "select gv.id, gv.general_id, gv.name, gv.content, gv.status, gv.publisher, " \
                            "e.id env_id, e.name env, e.prefix, e.notification, e.notification_token, e.is_callback, e.callback_token " \
                            "from general g, general_version gv, env e " \
                            "where gv.general_id = g.id and g.env_id = e.id and gv.id = %s order by gv.update_time desc limit 1 "
        to_publish_version_info = await self.mp.dml(to_publish_version_sql, (gps.version_id,))
        current_status = to_publish_version_info['status']
        if current_status != 'publishing':
            raise RunError(msg='当前版本不在发布状态，不能终止')
        cs = ConfigStatus(current_status)
        cs.switch('publish_failed')

        await self.mp.dml(
            "update general_version set status = %s, publisher = %s, modifier = %s where id = %s",
            (cs.state, user, user, gps.version_id)
        )

        await add_general_version_log(
            general_id=gps.general_id,
            version_id=gps.version_id,
            name='{} 终止发布'.format(to_publish_version_info['name']),
            status=cs.state,
            info='{} 开始发布，{} 终止发布'.format(to_publish_version_info['publisher'], user),
            user=user,
            update_time=now
        )

    async def rollback(self, **kwargs):
        gr = GeneralRollback(**kwargs)
        await GeneralCheck.general_not_found(general_id=gr.general_id)
        await GeneralCheck.rollback_forbidden(general_id=gr.general_id)
        await GeneralCheck.being_publishing_or_rollbacking(general_id=gr.general_id, detail='回滚')

        now = datetime.now()
        user = kwargs.get('user')

        to_rollback_version_sql = "select gv.id, gv.general_id, gv.name, gv.content, gv.status, " \
                            "e.id env_id, e.name env, e.prefix, e.notification, e.notification_token, e.is_callback, e.callback_token " \
                            "from general g, general_version gv, env e " \
                            "where gv.general_id = g.id and g.env_id = e.id and gv.id = %s order by gv.update_time desc limit 1 "
        to_rollback_version_info = await self.mp.dml(to_rollback_version_sql, (gr.version_id,))
        current_version_info = await self.mp.dml(
            "select * from general_version where general_id = %s order by update_time desc limit 1 ",
            (gr.general_id,)
            )

        if to_rollback_version_info['id'] == current_version_info['id']:
            raise RunError(msg='待回滚与当前版本相同，不能回滚')

        rollback_cs = ConfigStatus(to_rollback_version_info['status'])
        rollback_cs.switch('publishing')
        current_cs = ConfigStatus(current_version_info['status'])
        current_cs.switch('rollbacking')
        async with self.mp.pool.acquire() as conn:
            cur = await conn.cursor() 
            try:
                await cur.execute(
                    "update general_version set status = %s, publisher = %s, modifier = %s where id = %s",
                    (rollback_cs.state, user, user, to_rollback_version_info['id'])
                )
                await cur.execute(
                    "update general_version set status = %s, publisher = %s where id = %s",
                    (current_cs.state, user, current_version_info['id'])
                    )

                await conn.commit()
            except Exception as e:
                await conn.rollback()
                raise(e)

        await add_general_version_log(
            general_id=gr.general_id,
            version_id=to_rollback_version_info['id'],
            name='{} 正在回滚到 {}'.format(current_version_info['name'], to_rollback_version_info['name']),
            status=current_cs.state,
            info='',
            user=user,
            update_time=now
        )

        payload = {
            'current_cs': current_cs,
            'current_general_info': current_version_info
        }
        await notification(to_rollback_version_info, rollback_cs, user, is_rollback=True, **payload)
        await need_callback(to_rollback_version_info, rollback_cs, user, is_rollback=True, **payload)

    async def rollback_stop(self, **kwargs):
        gr = GeneralRollback(**kwargs)
        user = kwargs.get('user')
        now = datetime.now()
        await GeneralCheck.general_not_found(general_id=gr.general_id)

        previous_to_publish_version_sql = "select gv.id, gv.general_id, gv.name, gv.content, gv.status, gv.publisher, " \
                            "e.id env_id, e.name env, e.prefix, e.notification, e.notification_token, e.is_callback, e.callback_token " \
                            "from general g, general_version gv, env e " \
                            "where gv.general_id = g.id and g.env_id = e.id and gv.id = %s order by gv.update_time desc limit 1 "
        previous_to_publish_version_info= await self.mp.dml(previous_to_publish_version_sql, (gr.version_id,))
        current_need_rollback_version_info = await self.mp.dml(
            "select * from general_version where general_id = %s order by update_time desc limit 1 ",
            (gr.general_id,)
            )

        previous_need_publish_cs = ConfigStatus(previous_to_publish_version_info['status'])
        previous_need_publish_cs.switch('publish_failed')
        current_need_rollback_cs = ConfigStatus(current_need_rollback_version_info['status'])
        current_need_rollback_cs.switch('rollback_failed')

        async with self.mp.pool.acquire() as conn:
            cur = await conn.cursor() 
            try:
                sql = "update general_version set status = %s, publisher = %s, modifier = %s where id = %s"
                await cur.execute(
                    sql,
                    (previous_need_publish_cs.state, user, user, previous_to_publish_version_info['id'])
                )
                await cur.execute(
                    sql,
                    (current_need_rollback_cs.state, user, user, current_need_rollback_version_info['id'])
                    )

                await conn.commit()
            except Exception as e:
                await conn.rollback()
                raise(e)

        await add_general_version_log(
            general_id=gr.general_id,
            version_id=current_need_rollback_version_info['id'],
            name='{} 回滚到 {}，终止回滚'.format(current_need_rollback_version_info['name'], previous_to_publish_version_info['name']),
            status=current_need_rollback_cs.state,
            info='{} 开始回滚，{} 终止回滚'.format(previous_to_publish_version_info['publisher'], user),
            user=user,
            update_time=now
        )


    async def list_general_version_log(self, **kwargs):
        ret = {
            'logs': []
        }
        gvl = GeneralVersionLog(general_id=kwargs['general_id'])
        await GeneralCheck.general_not_found(general_id=gvl.general_id)
        list_version_log_sql = "select * from general_version_log where general_id = %s order by id desc limit 100"
        list_version_log_condition = (gvl.general_id,)
        ret['logs'] = await self.mp.dml(list_version_log_sql, list_version_log_condition, all=True)
        return ret


    async def fuzzysearch_general_version(self, condition, **kwargs):
        ret = {
            'general_version_list' : [],
            'general_version_counts': 0,
        }
        sql = "select a.id, a.name, c.name env, a.belongto, c.prefix, " \
            "b.name as version, b.content, b.update_time, b.modifier, b.publish_time, b.publisher " \
            "from general a, general_version b, env c " \
            "where a.env_id = c.id and a.id = b.general_id and b.content like CONCAT('%%', %s, '%%') order by b.update_time desc"
        cond = (condition,)
        res_list = await self.mp.dml(sql, cond, all=True)
        ret['general_version_counts'] = len(res_list)
        ret['general_version_list'] = res_list
        return ret

    async def render(self, **kwargs):
        ret = {
            'content': ''
        }
        gr = GeneralRender(**kwargs)

        sql = 'select g.*, gv.content, e.name env, e.prefix ' \
            'from general g, general_version gv, env e ' \
            'where g.id = gv.general_id and g.env_id = e.id ' \
            'and gv.general_id = %s and gv.id = %s and g.is_delete = 0 ' 
        current_general_version_info = await self.mp.dml(sql, (gr.general_id, gr.version_id))
        ret['content'] = await render_general(current_general_version_info['content'], current_general_version_info['env_id'])
        return ret


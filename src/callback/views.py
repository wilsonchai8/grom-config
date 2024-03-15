from src.asy.mysql_client import MysqlPool
from src.common.web_handler import get_loop
from src.common.meta import *
from src.common.exception_handler import RunError
from src.common.state_machine import *
from src.general.internal import add_general_version_log
from datetime import datetime


class GeneralCallback(ConfigMetaClass):
    code = MustInteger('code')
    msg = MustString('msg')
    payload = CouldBlank('payload')
    
    def __init__(self, *args, **kwargs) -> None:
        self.code = kwargs.get('code')
        self.msg = kwargs.get('msg')
        self.payload = kwargs.get('payload')

class Callback:

    def __init__(self) -> None:
        self.loop = get_loop()
        self.mp = MysqlPool(self.loop)

    async def general_callback(self, **kwargs):
        ret = {
            'code': 0,
            'msg': 'success'
        }
        gcb = GeneralCallback(**kwargs)
        if not gcb.payload:
            raise RunError(msg='payload is None')

        action = gcb.payload['action']
        general_info = await self.mp.dml(
            "select * from general_version where id = %s",
            (gcb.payload['version_id'],)
        )
        user = general_info['modifier']
        cs = ConfigStatus(general_info['status'])
        target_status = 'published' if gcb.code == 0 else 'publish_failed'
        cs.switch(target_status)
        status = cs.state

        if action == 'publish':
            now = datetime.now()
            title = '{} {}'.format(general_info['name'], states_to_name[status])
            await self.mp.dml(
                "update general_version set status = %s, publish_time = %s, publisher = %s, status = %s where id = %s ",
                (status, now, user, status, general_info['id'])
            )
        else:
            current_general_info = await self.mp.dml(
                "select * from general_version where id = %s",
                (gcb.payload['current_general_info']['version_id'],)
            )

            current_cs = ConfigStatus(current_general_info['status'])
            current_target_status = 'rollbacked' if gcb.code == 0 else 'rollback_failed'
            current_cs.switch(current_target_status)
            status = current_cs.state
            title = '{} 回滚到 {} {}'.format(current_general_info['name'], general_info['name'], states_to_name[status])

            async with self.mp.pool.acquire() as conn:
                cur = await conn.cursor() 
                try:
                    await cur.execute(
                        "update general_version set status = %s, publish_time = %s, publisher = %s, status = %s where id = %s ",
                        (status, datetime.now(), user, status, current_general_info['id'])
                    )

                    now = datetime.now()
                    general_sql = "update general_version set status = %s, update_time = %s, publish_time = %s, publisher = %s, status = %s where id = %s " \
                        if gcb.code == 0 \
                        else "update general_version set status = %s, publish_time = %s, publisher = %s, status = %s where id = %s "
                    general_conditions = (status, now, now, user, cs.state, general_info['id']) \
                        if gcb.code == 0 \
                        else (status, now, user, cs.state, general_info['id'])
                    await cur.execute(
                        general_sql, 
                        general_conditions
                    )

                    await conn.commit()
                except Exception as e:
                    await conn.rollback()
                    raise(e)

        await add_general_version_log(
            general_id=general_info['general_id'],
            version_id=general_info['id'],
            status=status,
            name=title,
            info=gcb.msg,
            user=user,
            update_time=now
        )

        return ret

    async def need_rollback(self, **kwargs):
        pass

from src.common.exception_handler import *
from src.asy.mysql_client import MysqlPool
from src.common.web_handler import get_loop
from .meta import GeneralVersionLogAdd, GeneralPublish
from .check import GeneralCheck
from datetime import datetime
from src.common.state_machine import *
from src.common.config import get_conf
import aiohttp
import re

async def render_general(general_content, env_id, is_render=True):
    render_content = general_content.split('\n')
    if is_render is True:
        temp_list = list()
        pattern = re.compile(r'<<<(.*?)>>>', re.S)
        comment_pattern = r'\#.*$'
        for line in render_content:
            res = re.search(comment_pattern, line)
            if res:
                comment_start = res.span()[0]
                content = line[:comment_start]
                comment = line[comment_start:]
            else:
                content = line
                comment = ''
            for item in re.findall(pattern, content):
                res = await get_public_item(item, env_id)
                value = res['v'] if res else ''
                content = content.replace('<<<{}>>>'.format(item), value)
            temp_list.append('{}{}'.format(content, comment))
        render_content = temp_list
    origin = '\n'.join(render_content)
    return origin

async def get_public_item(k, env_id):
    loop = get_loop()
    mp = MysqlPool(loop)

    sql = "select k, v from public_item pi, public_item_version piv " \
        "where pi.id = piv.public_item_id " \
        "and pi.k = %s and pi.env_id = %s and piv.status = 'published' "\
        "order by publish_time desc limit 1"
    return await mp.dml(sql, (k, env_id))



async def publish_flow(**kwargs):
    loop = get_loop()
    mp = MysqlPool(loop)
    now = datetime.now()

    gp = GeneralPublish(**kwargs)
    user = kwargs.get('user')
    await GeneralCheck.general_not_found(general_id=gp.general_id)
    await GeneralCheck.being_publishing_or_rollbacking(general_id=gp.general_id, detail='发布')

    to_publish_version_sql = "select gv.id, gv.general_id, gv.name, gv.content, gv.status, " \
                        "e.id env_id, e.name env, e.prefix, e.notification, e.notification_token, e.is_callback, e.callback_token " \
                        "from general g, general_version gv, env e " \
                        "where gv.general_id = g.id and g.env_id = e.id and gv.id = %s order by gv.update_time desc limit 1 "
    to_publish_version_info = await mp.dml(to_publish_version_sql, (gp.version_id,))

    cs = ConfigStatus(to_publish_version_info['status'])
    cs.switch('publishing')

    await mp.dml(
        "update general_version set status = %s, publish_time = %s, publisher = %s where id = %s",
        (cs.state, now, user, gp.version_id)
    )

    await add_general_version_log(
        general_id=gp.general_id,
        version_id=to_publish_version_info['id'],
        status=cs.state,
        name='{} {}'.format(to_publish_version_info['name'], states_to_name[cs.state]),
        info='',
        user=user,
        update_time=now
    )

    await notification(to_publish_version_info, cs, user)
    await need_callback(to_publish_version_info, cs, user)

async def notification(general_info, cs, user, is_rollback=False, **kwargs):
    loop = get_loop()
    mp = MysqlPool(loop)
    now = datetime.now()
    notification_addr = general_info['notification']
    if notification_addr:
        timeout_config = int(get_conf()['runtime']['notification_timeout'])
        callback_url_config = get_conf()['runtime']['callback_url']
        try:
            timeout = aiohttp.ClientTimeout(total=timeout_config)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                payload = {
                    'callback_url': callback_url_config,
                    'callback_token': general_info['callback_token'],
                    'general_id': general_info['general_id'],
                    'version_id': general_info['id'],
                    'version': general_info['name'],
                    'content': await render_general(general_info['content'], general_info['env_id']),
                    'env': general_info['env'],
                    'prefix': general_info['prefix'],
                    'action': 'publish' if not is_rollback else 'rollback',
                }
                if is_rollback:
                    rollback_general_info = kwargs['current_general_info']
                    payload['current_general_info'] = {
                        'general_id': rollback_general_info['general_id'],
                        'version_id': rollback_general_info['id'],
                        'version': rollback_general_info['name'],
                    }
                async with session.post(notification_addr, json=payload) as response:
                    if response.status != 200:
                        res_json = await response.text()
                        raise RuntimeError(res_json)
        except Exception as e:
            msg = '{} ---- {} {}'.format(notification_addr, e.__class__.__name__, e.args)
            title = '{} {}'.format(general_info['name'], states_to_name[cs.state]),
            cs.switch('publish_failed')
            status = cs.state

            await mp.dml(
                "update general_version set status = %s, publisher = %s where id = %s ",
                (cs.state, user, general_info['id'])
            )

            if is_rollback:
                current_cs = kwargs['current_cs']
                current_general_info = kwargs['current_general_info']
                current_cs.switch('rollback_failed')
                status = current_cs.state
                await mp.dml(
                    "update general_version set status = %s, publisher = %s where id = %s",
                    (current_cs.state, user, current_general_info['id'])
                )
                title = '{} 回滚到 {} 回滚失败'.format(current_general_info['name'], general_info['name'])

            await add_general_version_log(
                general_id=general_info['general_id'],
                version_id=general_info['id'],
                status=status,
                name=title,
                info=msg,
                user=user,
                update_time=now
            )

            raise RunError(msg=msg)

async def need_callback(general_info, cs, user, is_rollback=False, **kwargs):
    loop = get_loop()
    mp = MysqlPool(loop)
    now = datetime.now()
    is_callback = general_info['is_callback']
    status = cs.state
    title = '{} {}'.format(general_info['name'], states_to_name[cs.state]),
    if not is_callback:
        cs.switch('published')
        await mp.dml(
            "update general_version set status = %s, publish_time = %s, update_time = %s, publisher = %s where id = %s ",
            (cs.state, now, now, user, general_info['id'])
        )

        if is_rollback:
            current_cs = kwargs['current_cs']
            current_general_info = kwargs['current_general_info']
            current_cs.switch('rollbacked')
            status = current_cs.state
            await mp.dml(
                "update general_version set status = %s, publisher = %s where id = %s",
                (current_cs.state, user, current_general_info['id'])
            )
            title = '{} 回滚到 {} 回滚成功'.format(current_general_info['name'], general_info['name'])

        await add_general_version_log(
            general_id=general_info['general_id'],
            version_id=general_info['id'],
            status=status,
            name=title,
            info='',
            user=user,
            update_time=now
        )

async def add_general_version_log(**kwargs):
    loop = get_loop()
    mp = MysqlPool(loop)
    gvld = GeneralVersionLogAdd(**kwargs)
    list_version_log_sql = "insert into general_version_log(general_id, general_version_id, name, info, status, update_time, modifier) " \
                            "values(%s, %s, %s, %s, %s, %s, %s)"
    list_version_log_condition = (
        gvld.general_id,
        gvld.version_id,
        gvld.name,
        gvld.info,
        gvld.status,
        gvld.update_time,
        gvld.user,
    )
    await mp.dml(list_version_log_sql, list_version_log_condition)



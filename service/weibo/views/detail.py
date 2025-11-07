from utils.error_code import ErrorCode
from utils.reply import reply
from lib.logger import logger
from ..logic import request_detail
from ..models import accounts

# route
async def detail(id: str):
    """
    获取微博信息
    """
    # 优先使用已添加账号的cookie访问PC端AJAX，提高成功率
    _accounts = await accounts.load()
    has_unexpired_account = False
    for account in _accounts:
        if account.get('expired', 0) == 1:
            continue
        has_unexpired_account = True
        account_id = account.get('id', '')
        res, succ = await request_detail(id, account.get('cookie', ''))
        if not succ or res == {}:
            # 账号可能失效，标记过期
            await accounts.expire(account_id)
            logger.error(f'get weibo detail failed by account, account: {account_id}, id: {id}, res: {res}')
            continue
        logger.info(f'get weibo detail success by account, account: {account_id}, id: {id}')
        return reply(ErrorCode.OK, '成功', res)

    # 若无可用账号或账号请求失败，最后尝试移动端HTML解析（游客）
    res, succ = await request_detail(id)
    if not succ or res == {}:
        logger.error(f'get weibo detail failed by guest, id: {id}, res: {res}')
        # 若没有可用账号（未添加或全部过期），提示先添加账号
        if not has_unexpired_account:
            return reply(ErrorCode.NO_ACCOUNT, '请先添加账号')
        # 若存在账号但游客兜底仍失败，保留内部错误提示
        return reply(ErrorCode.INTERNAL_ERROR, '内部错误请重试')
    return reply(ErrorCode.OK, '成功', res)
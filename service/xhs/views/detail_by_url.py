from utils.error_code import ErrorCode
from utils.reply import reply
from ..models import accounts
from lib.logger import logger
from ..logic import request_detail_by_url
import random

# route
async def detail_by_url(url: str):
    """
    根据分享 URL 获取笔记详情
    """
    _accounts = await accounts.load()
    random.shuffle(_accounts)
    for account in _accounts:
        if account.get('expired', 0) == 1:
            continue
        account_id = account.get('id', '')
        res, succ = await request_detail_by_url(url, account.get('cookie', ''))
        if res == {} or not succ:
            logger.error(f'get note detail by url failed, account: {account_id}, url: {url}')
            continue
        logger.info(f'get note detail by url success, account: {account_id}, url: {url}, res: {res}')
        return reply(ErrorCode.OK, '成功', res)
    logger.warning(f'get note detail by url failed. url: {url}')
    return reply(ErrorCode.NO_ACCOUNT, '请先添加账号')
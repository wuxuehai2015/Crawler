from .common import common_request, COMMON_HEADERS
from lib import requests
from lib.logger import logger
from bs4 import BeautifulSoup
import re
import json



async def request_detail(id: str, cookie: str) -> tuple[dict, bool]:
    """
    请求小红书获取视频信息
    """
    # 获取xsec_token
    url = f'https://www.xiaohongshu.com/explore/{id}'
    headers = {"cookie": cookie}
    headers.update(COMMON_HEADERS)
    resp = await requests.get(url, headers=headers)
    if resp.status_code != 200 or resp.text == '':
        return {}, False
    try:
        soup = BeautifulSoup(resp.text, 'html.parser')
        pattern = re.compile('window\\.__INITIAL_STATE__={.*}')
        text = soup.body.find(
            'script', text=pattern).text.replace('window.__INITIAL_STATE__=', '').replace('undefined', '""')
        target = json.loads(text)
        detail_data = target.get('note', {}).get('noteDetailMap', {}).get(id, {})
    except Exception as e:
        logger.error(f"failed to get detail: {id}, err: {e}")
        return {}, False
    return detail_data, True


async def request_detail_by_url(url: str, cookie: str) -> tuple[dict, bool]:
    """
    通过给定的小红书笔记 URL 获取详情，跟随 302 并从最终页面的 HTML 中解析大 JSON。
    支持 PC 与移动分享链接。
    """
    headers = {"cookie": cookie}
    headers.update(COMMON_HEADERS)
    resp = await requests.get(url, headers=headers, follow_redirects=True)
    if resp.status_code != 200 or resp.text == '':
        logger.error(f"failed to fetch url detail, code: {resp.status_code}, url: {url}")
        return {}, False
    try:
        # 直接用正则从原始 HTML 中提取 JSON，避免 BeautifulSoup 对脚本内容的意外处理
        m = re.search(r'window\.__INITIAL_STATE__\s*=\s*(\{.*?\})', resp.text, re.S)
        if not m:
            logger.error(f"initial state script not found for url: {url}")
            return {}, False
        text = m.group(1)
        # 将非 JSON 的占位符替换为可解析的值
        # 小红书页面常出现 undefined 标记，替换为 null
        text = re.sub(r'(?<!["'])\bundefined\b', 'null', text)
        target = json.loads(text)
        detail_map = target.get('note', {}).get('noteDetailMap', {})
        # 优先使用 URL 中的 id，否则取 map 中的首个值
        m = re.search(r'/(explore|discovery/item)/([0-9a-z]+)', url)
        note_id = m.group(2) if m else None
        if note_id and note_id in detail_map:
            detail_data = detail_map.get(note_id, {})
        else:
            # 取第一个详情对象
            detail_data = next(iter(detail_map.values()), {})
        if detail_data == {}:
            logger.error(f"detail json not found from url: {url}")
            return {}, False
        return detail_data, True
    except Exception as e:
        logger.error(f"failed to parse url detail: {url}, err: {e}")
        return {}, False

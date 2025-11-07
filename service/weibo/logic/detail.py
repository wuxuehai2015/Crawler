from .common import mobile_common_request, HOST, COMMON_HEADERS
from lib import requests
import re
import json

async def request_detail(id: str, cookie: str = '') -> tuple[dict, bool]:
    """
    请求微博获取微博信息
    """
    # 尝试PC端AJAX（需要登录cookie）：直接返回接口原始JSON，不做 ok/data 判定
    if cookie:
        url = f"{HOST}/ajax/statuses/show"
        params = {"id": id}
        headers = {"cookie": cookie}
        headers.update(COMMON_HEADERS)
        resp = await requests.get(url, headers=headers, params=params)
        if resp.status_code == 200 and resp.text != '':
            try:
                data = resp.json()
            except Exception:
                pass
            else:
                # 仅当无 error 字段时认为成功，直接返回原始 JSON
                if not (isinstance(data, dict) and data.get('error')):
                    return data, True
        # PC失败则继续移动端HTML解析
    headers = {"Referer": f"https://m.weibo.cn/status/{id}"}
    resp, succ = await mobile_common_request(f'/detail/{id}', {}, headers, True)
    if not succ or not resp:
        resp, succ = await mobile_common_request(f'/status/{id}', {}, headers, True)
        if not succ:
            return {}, succ
    # 兼容新版页面：直接匹配数组，不强制 [0]
    match = re.search(r'var \$render_data\s*=\s*(\[.*?\])', resp, re.DOTALL)
    if match:
        try:
            text = match.group(1)
            data = json.loads(text)
            detail = (data[0] if isinstance(data, list) and len(data) > 0 else {}).get("status", {})
            return detail, True
        except Exception:
            pass
    # 兜底：尝试匹配 INITIAL_STATE
    match2 = re.search(r'window\.__INITIAL_STATE__\s*=\s*({.*?})', resp, re.DOTALL)
    if match2:
        try:
            state = json.loads(match2.group(1))
            detail = state.get('status', {})
            if detail:
                return detail, True
        except Exception:
            pass
    return {}, False
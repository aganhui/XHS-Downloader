import json
import os
from urllib import request
from urllib.error import HTTPError, URLError


def post_json(url: str, payload: dict, timeout: int = 30) -> tuple[int, str]:
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = request.Request(
        url,
        data=data,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )
    with request.urlopen(req, timeout=timeout) as resp:
        return resp.status, resp.read().decode("utf-8")


def main():
    url = os.getenv("XHS_BASE_URL", "https://xhs-downloader-nine.vercel.app")
    url = url.rstrip("/") + "/xhs/search"
    cookie = os.getenv("XHS_COOKIE")
    payload = {
        "keyword": "ha24msa",
        "require_num": 20,
        "sort_type_choice": 1,
        "note_type": 0,
        "note_time": 1,
        "note_range": 0,
        "pos_distance": 0,
    }
    if cookie:
        payload["cookie"] = cookie
    try:
        status, body = post_json(url, payload, timeout=60)
        print(f"status={status}")
        # print(body)
        print(json.loads(body)["data"][0])
    except HTTPError as exc:
        body = exc.read().decode("utf-8")
        print(f"status={exc.code}")
        print(body)
    except URLError as exc:
        print(f"request failed: {exc}")
    except Exception as exc:
        print(f"request failed: {exc}")

# Response: {'xsec_token': 'ABWa494Czq4PA4SC5n-CvjqiLuIBY1x2ZGrXVv1C4scrw=', 'id': '6985d903000000000e03c574', 'model_type': 'note', 'note_card': {'cover': {'height': 1600, 'width': 1200, 'url_default': 'http://sns-webpic-qc.xhscdn.com/202602062146/22b7ac9f8b69067218b54288023c9ca5/notes_pre_post/1040g3k031s8cungslk004a8rudd41jf74ok42ig!nc_n_webp_mw_1', 'url_pre': 'http://sns-webpic-qc.xhscdn.com/202602062146/253c8e8c965ac367c76ff4b97f8f3af7/notes_pre_post/1040g3k031s8cungslk004a8rudd41jf74ok42ig!nc_n_webp_prv_1'}, 'image_list': [{'height': 1600, 'width': 1200, 'info_list': [{'image_scene': 'WB_DFT', 'url': 'http://sns-webpic-qc.xhscdn.com/202602062146/22b7ac9f8b69067218b54288023c9ca5/notes_pre_post/1040g3k031s8cungslk004a8rudd41jf74ok42ig!nc_n_webp_mw_1'}, {'image_scene': 'WB_PRV', 'url': 'http://sns-webpic-qc.xhscdn.com/202602062146/253c8e8c965ac367c76ff4b97f8f3af7/notes_pre_post/1040g3k031s8cungslk004a8rudd41jf74ok42ig!nc_n_webp_prv_1'}]}], 'corner_tag_info': [{'type': 'publish_time', 'text': '1小时前'}], 'type': 'normal', 'user': {'nickname': 'Catherine_cc', 'xsec_token': 'AB_MQfkxCOp2aaLuYbssEaAAdwTGkQmAYmSViiCAqzYZo=', 'nick_name': 'Catherine_cc', 'avatar': 'https://sns-avatar-qc.xhscdn.com/avatar/1040g2jo31kf8t9ap2u004a8rudd41jf7m5v1h60?imageView2/2/w/80/format/jpg', 'user_id': '5b645a4011be106a0a96cde7'}, 'interact_info': {'collected_count': '0', 'comment_count': '0', 'shared_count': '0', 'liked': False, 'liked_count': '0', 'collected': False}}, 'note_url': 'https://www.xiaohongshu.com/explore/6985d903000000000e03c574?xsec_token=ABWa494Czq4PA4SC5n-CvjqiLuIBY1x2ZGrXVv1C4scrw='}


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
import re
from time import sleep
import requests
import urllib
import time
import pause
from collections import Counter
import matplotlib.pyplot as plt
from wordcloud import WordCloud

USER_AGENT = {'User-Agent' : 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_4) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/11.1 Safari/605.1.15'}
FIND_TAG_REGEX = "#[A-z0-9_ㄱ-힣]+"
FONT_PATH = "/Library/Fonts/AppleGothic.ttf"
SEARCH_TARGET_TAG = "동산병원"
LIMIT_TIME = 86400
TAG_LIMIT_COUNT = 50

instagram_tags = []
_start_time = 0

def remove_apostrophes(param):
    if "\'" in param:
        param = param.replace("\'", "")

    if "\\" in param:
        param = param.replace("\\", "")

    return param

def get_location_contents(json_container):

    json_hash_media = json_container["edge_hashtag_to_media"]
    content_page_info = json_hash_media["page_info"]

    posts = json_hash_media["edges"]  # 콘텐츠 스토리지
    end_cursor = ""

    if content_page_info["has_next_page"] != False:
        end_cursor = content_page_info["end_cursor"]

    for post in posts:

        comp_time = _start_time - int(post["node"]["taken_at_timestamp"])

        if comp_time < LIMIT_TIME:
            if len(post["node"]["edge_media_to_caption"]["edges"]) > 0:
                content = str(post["node"]["edge_media_to_caption"]["edges"][0]["node"]["text"])
                tag_regex = re.compile(FIND_TAG_REGEX)
                tags = tag_regex.findall(content)

                for tag in tags:
                    tag_none_hashtag = tag.replace("#", "")
                    instagram_tags.append(tag_none_hashtag)
        else:
            end_cursor = ""
            break

    return end_cursor

def get_json(hashtag_param, end_cursor):
    if end_cursor == "":
        req_url = "https://www.instagram.com/explore/tags/" + str(hashtag_param) + "/?__a=1"

    else:
        paging_query_hash = "463d0b9e24ab084f46514747d53bcb0d"  ### constant value
        paging_param_first = 12
        paging_param_after = end_cursor

        base_url = "https://www.instagram.com/graphql/query/?query_hash=" + paging_query_hash + "&variables="
        url_variables = "{\"tag_name\":\"" + str(hashtag_param) + "\",\"first\":\"" + str(
            paging_param_first) + "\",\"after\":\"" + paging_param_after + "\"}"
        encoded_url_variables = urllib.parse.quote(str(url_variables))

        req_url = base_url + encoded_url_variables

    response = requests.get(req_url, headers=USER_AGENT, timeout=15.0)

    json_data = response.json()

    if end_cursor == "":
        json_location = json_data["graphql"]["hashtag"]
    else:
        json_location = json_data["data"]["hashtag"]

    if len(json_location) != 0:
        if len(json_location["edge_hashtag_to_media"]) != 0:
            return json_location

def main():
    global instagram_tags
    global _start_time

    _start_time = int(time.time())
    pause.until(_start_time)
    end_cursor = ""
    
    while True:
        json_value = get_json(SEARCH_TARGET_TAG, end_cursor)

        end_cursor = get_location_contents(json_value)

        if end_cursor == "":
            break

        sleep(3)

    instagram_tags = [word for word in instagram_tags]
    count = Counter(instagram_tags)

    common_tag = count.most_common(TAG_LIMIT_COUNT)

    wc = WordCloud(font_path=FONT_PATH, background_color="white", width=800, height=600)
    cloud = wc.generate_from_frequencies(dict(common_tag))

    plt.imshow(cloud)
    plt.axis('off')
    plt.figure()
    plt.show()

if __name__ == '__main__':
    main()
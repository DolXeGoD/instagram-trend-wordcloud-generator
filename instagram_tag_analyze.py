# -*- coding: utf-8 -*-
import os
import re
import urllib
import time
from collections import Counter
import requests
from wordcloud import WordCloud
import datetime

# 유저 에이전트
USER_AGENT = {'User-Agent' : 'Mozilla/5.0 (iPhone; CPU iPhone OS 13_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 Instagram 177.0.0.20.117 (iPhone12,1; iOS 13_6; ru_RU; ru-RU; scale=2.00; 828x1792; 275424340)'}

# 크롤링 시작 시간
STARTED_TIME = int(time.time())

# 해쉬태그 탐색 정규식
FIND_TAG_REGEX = "#[A-z0-9_ㄱ-힣]+"

# wordcloud에 사용될 폰트
FONT_PATH = "/Library/Fonts/AppleGothic.ttf"

# 크롤링 대상 게시글의 등록일자 시간 제한
# - 크롤링 시작시점을 기준으로 최대 LIMIT_TIME(unix_timestamp) 안에 등록된 게시글을 대상으로만 크롤링 진행
LIMIT_TIME = 86400

# wordcloud 에 보여질 단어의 제한 갯수
TAG_LIMIT_COUNT = 50

# 인스타그램 request timeout 
REQUEST_TIMEOUT = 15

# 인스타그램 게시글 페이징 필수 값
PAGING_QUERY_HASH = "463d0b9e24ab084f46514747d53bcb0d"

# 추출된 해쉬태그를 저장하는 리스트
INSTAGRAM_TAGS = []

def remove_apostrophes(param):
    if "\'" in param:
        param = param.replace("\'", "")

    if "\\" in param:
        param = param.replace("\\", "")

    return param


def find_next_page_edges(edge_hashtag_to_media):
    end_cursor = ""
    content_page_info = edge_hashtag_to_media["page_info"]

    if content_page_info["has_next_page"] is not False:
        end_cursor = content_page_info["end_cursor"]

    return end_cursor


def find_hashtag_in_post(posts):
    for post in posts:
        comp_time = STARTED_TIME - int(post["node"]["taken_at_timestamp"])

        if comp_time < LIMIT_TIME:
            if len(post["node"]["edge_media_to_caption"]["edges"]) > 0:
                content = str(post["node"]["edge_media_to_caption"]["edges"][0]["node"]["text"])
                tag_regex = re.compile(FIND_TAG_REGEX)
                tags = tag_regex.findall(content)

                for tag in tags:
                    tag_none_hashtag = tag.replace("#", "")
                    INSTAGRAM_TAGS.append(tag_none_hashtag)
        else:
            return False

    return True


def get_json(search_target_tag, end_cursor):
    if end_cursor == "":
        req_url = "https://www.instagram.com/explore/tags/" + str(search_target_tag) + "/?__a=1"

    else:
        paging_param_first = 12

        base_url = "https://www.instagram.com/graphql/query/?query_hash=" + PAGING_QUERY_HASH + "&variables="

        url_variables = "{\"tag_name\":\"" + str(search_target_tag) + "\",\"first\":\"" + str(
            paging_param_first) + "\",\"after\":\"" + end_cursor + "\"}"

        encoded_url_variables = urllib.parse.quote(str(url_variables))

        req_url = base_url + encoded_url_variables

    response = requests.get(req_url, headers=USER_AGENT, timeout=REQUEST_TIMEOUT)

    json_data = response.json()

    if end_cursor == "":
        json_location = json_data["graphql"]["hashtag"]
    else:
        json_location = json_data["data"]["hashtag"]

    if len(json_location) != 0:
        if len(json_location["edge_hashtag_to_media"]["edges"]) > 0:
            return json_location


def save_word_cloud_to_file(search_target_tag, cloud):
    if not os.path.isdir("wordcloud_result"):
        os.makedirs(os.path.join("wordcloud_result"))

    file_name = "wc_result_of_{0}_{1}".format(search_target_tag, datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))
    cloud.to_file("wordcloud_result/{}.png".format(file_name))

    print("디렉토리에 워드클라우드 이미지를 저장하였습니다.")


def generate_word_cloud():
    most_common_tag = Counter(INSTAGRAM_TAGS).most_common(TAG_LIMIT_COUNT)
    word_cloud = WordCloud(font_path=FONT_PATH, background_color="white", width=800, height=600)
    cloud = word_cloud.generate_from_frequencies(dict(most_common_tag))

    print("워드클라우드 생성이 완료되었습니다.")

    return cloud


def main():
    search_target_tag = input("분석할 태그명을 입력해주세요 : ")

    end_cursor = ""
    print("인스타그램에서 데이터 크롤링을 시작합니다...")
    while True:
        json_value = get_json(search_target_tag, end_cursor)

        end_cursor = find_next_page_edges(json_value["edge_hashtag_to_media"])
        is_continue = find_hashtag_in_post(json_value["edge_hashtag_to_media"]["edges"])

        if end_cursor == "" or is_continue is False:
            print("데이터 크롤링이 완료되었습니다.")
            break

        time.sleep(3)

    print("워드클라우드 생성중...")
    cloud = generate_word_cloud()
    save_word_cloud_to_file(search_target_tag, cloud)


if __name__ == '__main__':
    main()

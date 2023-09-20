import requests
import json
from pprint import pprint
from kafka import KafkaProducer
import logging
from constants import YOUTUBE_API_KEY, PLAYLIST_ID


def fetch_page(url, parameters, page_token=None):
    params = {**parameters, 'key': YOUTUBE_API_KEY, 'page_token': page_token}
    response = requests.get(url, params)
    payload = json.loads(response.text)
    logging.info("Response +> %s", payload)

    return payload


def fetch_page_lists(url, parameters, page_token=None):
    while True:
        payload = fetch_page(url, parameters, page_token)
        yield from payload['items']

        page_token = payload.get('nextPageToken')
        if page_token is None:
            break


def format_response(video):
    video_res = {
        'title': video['snippet']['title'],
        'likes': int(video['statistics'].get('likeCount', 0)),
        'comments': int(video['statistics'].get('commentCount', 0)),
        'views': int(video['statistics'].get('viewCount', 0)),
        'favoriteCount': int(video['statistics'].get('favoriteCount', 0))
        # 'thumbnail': video['snippet']['default']['url']
    }
    return video_res


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    producer = KafkaProducer(boostrap_servers=['localhost:9092'])
    # response = requests.get("https://www.googleapis.com/youtube/v3/videos",
    #                         {
    #                             'key': YOUTUBE_API_KEY,
    #                             'id': "nOFbYhTVUn8",
    #                             'part': 'snippet,statistics,status'
    #                         })
    #
    # # print(response.text)
    # response = json.loads(response.text)['items']
    #
    # for video in response:

    #
    #     print(pprint(video_res))
    #
    #     producer.send('youtube_videos', json.dumps(video_res).encode('utf-8'))
    #     producer.flush()
    for video_item in fetch_page_lists(
            "https://www.googleapis.com/youtube/v3/playlistItems",
            {
                'playlistId': PLAYLIST_ID,
                'part': 'snippet,contentDetails'},
            None):
        video_id = video_item['contentDetails']['videoId']

        for video in fetch_page_lists(
                "https://www.googleapis.com/youtube/v3/videos",
                {'id': video_id, 'part': 'snippet,statistics'},
                None):
            # logging.info("video here => %s", pprint(format_response(video)))
            producer.send('youtube_videos', json.dumps(format_response(video)).encode('utf-8'),
                          key=video_id.encode('utf-8'))
            # producer.flush()
    #
    # response = requests.get("https://www.googleapis.com/youtube/v3/playlistItems",
    #             {
    #                         'key': YOUTUBE_API_KEY,
    #                         'playlistId': PLAYLIST_ID,
    #                         'part': 'snippet,contentDetails,status',
    #                         'page_token': 'nextpagetoken'
    #                     })
    # print(response.text)

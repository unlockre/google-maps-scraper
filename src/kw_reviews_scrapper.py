import logging
import time
import requests
import datetime
import json

def get_prop_id(url):
    from urllib.parse import urlparse

    # Parse the URL
    parsed_url = urlparse(url)

    # Extract the path segments
    path_segments = parsed_url.path.split('/')

    # Find the segment that starts with "data"
    data_param = next((segment for segment in path_segments if segment.startswith("data")), None)

    if data_param:
        segments = data_param.split("!")
        result = next((segment for segment in segments if segment.startswith("1s") and ":" in segment), None)
        return result
    return None


def get_reviews(place_id, page_token = ""): 

    if not page_token:
        page_token = ""

    url = f"https://www.google.com/maps/rpc/listugcposts?authuser=0&hl=en&gl=ar&pb=!1m6!{place_id}!6m4!4m1!1e1!4m1!1e3!2m2!1i20!2s{page_token}!5m2!1sM1EyZ5jkBeSj5NoPh-ufkQM!7e81!8m5!1b1!2b1!3b1!5b1!7b1!11m4!1e3!2e1!6m1!1i2!13m1!1e2"

    payload = {}
    headers = {
    'accept': '*/*',
    'accept-language': 'en-US,en;q=0.9',
    'priority': 'u=1, i',
    'referer': 'https://www.google.com/',
    'sec-ch-prefers-color-scheme': 'light',
    'sec-ch-ua': '"Chromium";v="130", "Google Chrome";v="130", "Not?A_Brand";v="99"',
    'sec-ch-ua-arch': '"arm"',
    'sec-ch-ua-bitness': '"64"',
    'sec-ch-ua-form-factors': '"Desktop"',
    'sec-ch-ua-full-version': '"130.0.6723.92"',
    'sec-ch-ua-full-version-list': '"Chromium";v="130.0.6723.92", "Google Chrome";v="130.0.6723.92", "Not?A_Brand";v="99.0.0.0"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-model': '""',
    'sec-ch-ua-platform': '"macOS"',
    'sec-ch-ua-platform-version': '"15.0.0"',
    'sec-ch-ua-wow64': '?0',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
    'x-goog-ext-353267353-jspb': '[null,null,null,147535]',
    'x-maps-diversion-context-bin': 'CAE='
    }

    response = requests.request("GET", url, headers=headers, data=payload)

    return response.text

def safe_extract(data, *path, default=None):
    try:
        for key in path:
            data = data[key]
        return data
    except (IndexError, KeyError, TypeError):
        return default

def get_reviews_and_next_page_token(place_id, page_token = ""):
    reviews = get_reviews(place_id, page_token)

    json_list = reviews.split(")]}'\n")
    content = json_list[1]

    data_raw = json.loads(content)
    next_page_token = data_raw[1]
    data_raw = data_raw[2]

    reviews = []
    for i, element in enumerate(data_raw):
                data = {
                    "review_id": safe_extract(data_raw, i, 0, 0),
                    "user_name": safe_extract(data_raw, i, 0, 1, 4, 5, 0, default=""),
                    "review_text": safe_extract(data_raw, i, 0, 2, 15, 0, 0, default=""),
                    "rating": safe_extract(data_raw, i, 0, 2, 0, 0),
                    "published_at_date": safe_extract(data_raw, i, 0, 1, 3),
                    "review_link": safe_extract(data_raw, i, 0, 4, 3, 0),
                    "response_from_owner_date": safe_extract(data_raw, i, 0, 3, 2),
                    "response_from_owner_text": safe_extract(data_raw, i, 0, 3, 14, 0, 0),
                    "published_at": "",
                    "review_likes_count": 0
                }
                if data["response_from_owner_date"]:
                    data["response_from_owner_date"] = datetime.datetime.fromtimestamp(data["response_from_owner_date"] / 1000000).strftime('%Y-%m-%d %H:%M:%S.%f')

                if data["published_at_date"]:
                    data["published_at_date"] = datetime.datetime.fromtimestamp(data["published_at_date"] / 1000000).strftime('%Y-%m-%d %H:%M:%S.%f')
                
                reviews.append(data)

    return reviews, next_page_token


def get_all_reviews(place_id, review_until=None):
    all_reviews = []
    next_page_token = ""

    while True: 
        reviews, next_page_token = get_reviews_and_next_page_token(place_id, next_page_token)
        all_reviews.extend(reviews)
        if not next_page_token:
            break
        if review_until:
            try:
                review_until_date = datetime.datetime.strptime(review_until, '%Y-%m-%d')
                last_review_date = datetime.datetime.strptime(reviews[-1]["published_at_date"], '%Y-%m-%d %H:%M:%S.%f')
                if last_review_date < review_until_date:
                    break
            except:
                logging.error(f"Error parsing review_until date: {review_until}. Retrieving all reviews.")
                pass

    return all_reviews


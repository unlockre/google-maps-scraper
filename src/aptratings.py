from datetime import datetime
from botasaurus.browser import browser, Driver
from botasaurus.request import request, Request
import bs4
import os
import json

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

ZENROWS_USER = os.environ.get("ZENROWS_USER")
ZENROWS_PWD = os.environ.get("ZENROWS_PWD")
PROXY_SERVICE_API_KEY = os.environ.get("PROXY_SERVICE_API_KEY")

# Validate environment variables
missing_vars = [
    var_name for var_name, value in {
        "ZENROWS_USER": ZENROWS_USER,
        "ZENROWS_PWD": ZENROWS_PWD,
        "PROXY_SERVICE_API_KEY": PROXY_SERVICE_API_KEY,
    }.items() if value is None
]

def extract_review_data(review_object):
    data = {}

    # Extract Review Creation Date
    if 'dates' in review_object and 'earliest_create_date_dt' in review_object['dates']:
        data['review_creation_date'] = review_object['dates']['earliest_create_date_dt']["time"]
    if 'review_creation_date' in data:
        data['review_creation_date'] = datetime.fromtimestamp(data['review_creation_date'] / 1000).isoformat()

    # Extract Review Text
    if 'strings' in review_object and 'review_text_s' in review_object['strings']:
        data['review_text'] = review_object['strings']['review_text_s']
    elif 'text' in review_object:
        data['review_text'] = review_object['text']

    # Extract Rating
    if 'floats' in review_object and 'rating_overall_f' in review_object['floats']:
        data['rating'] = review_object['floats']['rating_overall_f']

    # Extract Writer
    if 'strings' in review_object and 'author_s' in review_object['strings']:
        data['writer'] = review_object['strings']['author_s']

    # Extract Review ID
    if 'id' in review_object:
        data['review_id'] = review_object['id']

    # Extract Owner Response
    if 'strings' in review_object and 'response_text_s' in review_object['strings']:
        data['owner_response'] = review_object['strings']['response_text_s']

    # Extract Owner Response Date
    if 'dates' in review_object and 'response_date_created_dt' in review_object['dates']:
        data['owner_response_date'] = review_object['dates']['response_date_created_dt']["time"]
    if 'owner_response_date' in data:
        data['owner_response_date'] = datetime.fromtimestamp(data['owner_response_date'] / 1000).isoformat()

    return data

def extract_reviews_from_html(html):
    soup = bs4.BeautifulSoup(html, 'html.parser')
    scripts = soup.find_all('script')
    reviews = []
    
    for script in scripts:
        if "searchReviews" in script.text:
            queries = json.loads(script.text).get('props').get('pageProps').get('dehydratedState').get('queries')
            for query in queries:
                if "searchReviews" in query.get('queryHash'):
                    for r in query.get('state').get('data').get('reviews'):
                        review = extract_review_data(r[0])
                        reviews.append(review)
    return reviews


def parse_pagination_info(html_content):
    soup = bs4.BeautifulSoup(html_content, 'html.parser')
    
    # Find the main pagination container
    pagination_container = soup.find('div', class_='pagination')
    
    # Extract total reviews
    results_text = pagination_container.find('div', class_='Styles__Results-sc-1s0ur21-2').text
    total_reviews = int(results_text.split('of')[1].strip().split()[0])
    
    # Extract total pages by counting the page buttons
    page_buttons = pagination_container.find_all('span', class_='Styles__ButtonText-sc-1s0ur21-4')
    total_pages = max(int(button.text) for button in page_buttons if button.text.isdigit())
    
    return total_reviews, total_pages

def fetch_reviews(url, fetch_html_func):
    html = fetch_html_func(url)
    reviews = []

    total_reviews, total_pages = parse_pagination_info(html)
    reviews.extend(extract_reviews_from_html(html))
    print(total_reviews, total_pages)

    for page in range(2, total_pages + 1):
        new_url = f"{url}?page={page}"
        print(new_url)
        html = fetch_html_func(new_url)
        reviews.extend(extract_reviews_from_html(html))

    return reviews

@browser(proxy=f"http://{ZENROWS_USER}:{ZENROWS_PWD}@superproxy.zenrows.com:1337")
def get_apartmentratings_reviews(driver: Driver, data):
    url = data['url']
    return fetch_reviews(url, lambda u: driver.get(u) or driver.page_html)

@request()
def get_apartmentratings_reviews_request(request: Request, data):
    url = data.get('url')
    if not url:
        raise ValueError("The 'url' field is required in the input data.")

    if not PROXY_SERVICE_API_KEY:
        raise EnvironmentError("Missing PROXY_SERVICE_API_KEY environment variable.")

    headers = {
        'Authorization': PROXY_SERVICE_API_KEY,
        'Content-Type': 'application/json'
    }
    payload = {
        "url": url,
        "method": "GET",
        "proxy_source": "zenrows",
        "response_type": "html",
        "proxy_settings": {
            "asp": True,
            "premium_proxy": True
        }
    }

    def fetch_html_func(u):
        payload["url"] = u
        try:
            response = request.post(
                url='https://proxy-service.whykeyway.com/get_data',
                headers=headers,
                data=json.dumps(payload),
                timeout=80,
                json=True,
                browser='chrome'
            )
        except Exception as e:
            print(f"Error fetching HTML: {e}")
            raise

        return response.text

    return fetch_reviews(url, fetch_html_func)

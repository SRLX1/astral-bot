import requests,json, html,re
from config import NASA_API_KEY
from datetime import datetime
from zoneinfo import ZoneInfo

# print(NASA_API_KEY)
_cache = {"date":None, "data":None}

#uses regex to strip the html tags
def strip_html(html_text):
    html_text = html_text.split("<br><br>")[0]
    html_text = re.sub(r"<[^>]+>", "", html_text)  
    html_text = html.unescape(html_text).replace("\xa0", " ")
    html_text = re.sub(r"^Explanation:\s*", "", html_text)
    return html_text.strip()

#uses regex to strip all html tags apart from links
#links are converted to markdown format which can be read by discord
def strip_html_convert_links(html_text):
    def replace_link(match):
        url = match.group(1).strip().replace(" ", "%20")
        text = match.group(2).strip()
        return f"[{text}]({url})"

    html_text = re.sub(
        r'<a\s+[^>]*href="([^"]+)"[^>]*>(.*?)</a>',
        replace_link,
        html_text,
        flags=re.S,
    )
    html_text = re.sub(r"<[^>]+>", "", html_text)
    return html.unescape(html_text).strip()

#uses regext to strip all text and retrurn the link to the video file
#links are converted to be valid protocol or to a valid youtube link
def extract_video_url(basic_html):
    match = re.search(r'<(?:source|video|iframe)[^>]+src="([^"]+)"', basic_html, re.I)
    if not match:
        return None
    url = html.unescape(match.group(1))
    if url.startswith("//"):
        url = "https:" + url
    if "youtube.com/embed/" in url:
        video_id = url.split("youtube.com/embed/")[1].split("?")[0]
        url = f"https://www.youtube.com/watch?v={video_id}"
    return url

#gets the date in the eastern timezone in the correct format
#this is becauase nasa's api update at midnight eastern time. therfore if your timezone is different this needs to be accounted for
def nasa_date():
    return datetime.now(ZoneInfo("America/New_York")).strftime("%Y-%m-%d")

# Astrophotography of the day API endpoint
# GET https://science.nasa.gov/wp-json/wp/v2/apod-basic
def APOD_API_request(date=None):
    url = "https://science.nasa.gov/wp-json/wp/v2/apod-basic"
    params = {
        "api_key": NASA_API_KEY,
        "date": date or nasa_date(),
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()  # Raise an exception for HTTP errors
        data = response.json() # converts the respose to json format
        entry = data[0] if isinstance(data, list) else data # the endpoint returns multiple entries for previous days this takes the firs/newest one
    except requests.Timeout:
        print("NASA API request timed out")
        return None
    except requests.RequestException as e:
        print(f"NASA API request failed: {e}")
        return None
    return {
        "date": entry["date"],
        "title": entry["title"],
        "explanation": strip_html_convert_links(entry["explanation"]),
        "credit": strip_html_convert_links(entry["credit"]),
        "image_url": entry.get("hdurl"),
        "page_url": entry["permalink"],
        "hdurl": entry.get("hdurl", ""),
        "alt": entry.get("alt", ""),
        "media_type": entry["media_type"],
        "video": extract_video_url(entry.get("basic_html", "")) if entry["media_type"] == "video" else None,

    }

    # checks if the apod has been cached for today before making an api request
    # if it has been cached return the cache if not make and return the api request
def get_aopd():
    today = nasa_date()
    if _cache["date"] == today and _cache["data"]:
        return _cache["data"]
    data = APOD_API_request()
    if data:
        _cache["date"] = today
        _cache["data"] = data
    return data or _cache["data"]

# test because it will only run if the file is run directly
if __name__ == "__main__":
    apod_data = APOD_API_request()
    if apod_data:
        print(json.dumps(apod_data, indent=2, ensure_ascii=False))
#        print(apod_data)


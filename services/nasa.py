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
    if not html_text: return ""
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
    match = re.search(r'<(?:source|video|iframe)[^>]+src=["\']([^"\']+)["\']', basic_html, re.I)
    if not match:
        return None
    url = html.unescape(match.group(1)).strip()
    if url.startswith("//"):
        url = "https:" + url
    yt_match = re.search(r'(?:youtube(?:-nocookie)?\.com\/(?:embed\/|watch\?v=)|youtu\.be\/)([a-zA-Z0-9_-]{11})', url, re.I)
    if yt_match:
        video_id = yt_match.group(1)
        url = f"https://www.youtube.com/watch?v={video_id}"
    return url

#gets the date in the eastern timezone in the correct format
#this is becauase nasa's api update at midnight eastern time. therfore if your timezone is different this needs to be accounted for
def nasa_date():
    return datetime.now(ZoneInfo("America/New_York")).strftime("%Y-%m-%d")

# Helper to extract YouTube video ID and build thumbnail URL (checks for highest resolution available)
def get_youtube_thumbnail(video_url: str | None) -> str | None:
    if not video_url: return None
    match = re.search(r'(?:youtube\.com\/(?:embed\/|watch\?v=)|youtu\.be\/)([a-zA-Z0-9_-]{11})', video_url)
    if not match: return None
    video_id = match.group(1)

    # Check for higher-resolution thumbnails first:
    # maxresdefault (1080p / 720p HD), sddefault (640x480 SD), hqdefault (480x360)
    for quality in ("maxresdefault", "sddefault"):
        url = f"https://img.youtube.com/vi/{video_id}/{quality}.jpg"
        try:
            res = requests.head(url, timeout=2)
            if res.status_code == 200:
                return url
        except requests.RequestException:
            pass
    return f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"

def truncate_explanation(text, page_url, max_length=3400):
    if not text:
        return "No explanation provided."
    if len(text) <= max_length:
        return text
    trimmed = text[:max_length].rsplit(" ", 1)[0]
    if trimmed.count("[") > trimmed.count("]"):
        trimmed = trimmed.rsplit("[", 1)[0].rstrip()
    suffix = f"...\n\n[Read full explanation on NASA]({page_url})" if page_url else "..."
    return f"{trimmed}{suffix}"


# Helper to extract image or gif URL from basic_html when hdurl is missing or placeholder
def extract_image_url(basic_html):
    if not basic_html:
        return None
    match = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', basic_html, re.I)
    if not match:
        return None
    url = html.unescape(match.group(1)).strip()
    if url.startswith("//"):
        url = "https:" + url
    return url

# Astrophotography of the day API endpoint
# GET https://science.nasa.gov/wp-json/wp/v2/apod-basic
def APOD_API_request(date=None):
    url = "https://science.nasa.gov/wp-json/wp/v2/apod-basic"
    params = {"api_key": NASA_API_KEY}
    if date:
        # endpoint ignores "date"; it filters with date_from/date_to in YYMMDD format (e.g. 240101)
        yymmdd = datetime.strptime(date, "%Y-%m-%d").strftime("%y%m%d")
        params["date_from"] = params["date_to"] = yymmdd

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()  # Raise an exception for HTTP errors
        data = response.json() # converts the respose to json format
        if isinstance(data, list) and not data:
            print(f"No APOD found for {date}")
            return None
        entry = data[0] if isinstance(data, list) else data # the endpoint returns multiple entries for previous days this takes the firs/newest one
    except requests.Timeout:
        print("NASA API request timed out")
        return None
    except requests.RequestException as e:
        print(f"NASA API request failed: {e}")
        return None
    
    raw_video = extract_video_url(entry.get("basic_html", "")) or entry.get("url")
    video_url = raw_video if entry.get("media_type") == "video" else None
    if video_url:
        yt_match = re.search(r'(?:youtube(?:-nocookie)?\.com\/(?:embed\/|watch\?v=)|youtu\.be\/)([a-zA-Z0-9_-]{11})', video_url, re.I)
        if yt_match:
            video_url = f"https://www.youtube.com/watch?v={yt_match.group(1)}"

    thumbnail_url = get_youtube_thumbnail(video_url) if video_url else None
    explination = truncate_explanation(strip_html_convert_links(entry.get("explanation")), entry["permalink"])

    raw_hdurl = entry.get("hdurl")
    is_placeholder = bool(raw_hdurl and "news-thumbnail" in raw_hdurl)
    hdurl = None if is_placeholder else raw_hdurl

    fallback_image = extract_image_url(entry.get("basic_html", "")) or entry.get("image")
    image_url = hdurl or fallback_image

    return {
        "date": entry["date"],
        "title": entry["title"],
        "explanation": explination,
        "credit": strip_html_convert_links(entry.get("credit")) or "Public Domain",
        "image_url": image_url,
        "url": fallback_image or entry.get("url", ""),
        "hdurl": hdurl or fallback_image or "",
        "page_url": entry["permalink"],
        "alt": entry.get("alt", ""),
        "media_type": entry["media_type"],
        "video": video_url,
        "thumbnail_url": thumbnail_url
    }

    # checks if the apod has been cached for today before making an api request
    # if it has been cached return the cache if not make and return the api request
def get_aopd(date=None):
    today = nasa_date()
    if date and date != today:
        return APOD_API_request(date)
    if _cache["date"] == today and _cache["data"]:
        return _cache["data"]
    data = APOD_API_request()
    if data:
        if data.get("date") == today:
            _cache["date"] = today
            _cache["data"] = data
        return data
    return _cache["data"]

# test because it will only run if the file is run directly
if __name__ == "__main__":
    apod_data = APOD_API_request()
    if apod_data:
        print(json.dumps(apod_data, indent=2, ensure_ascii=False))
#        print(apod_data)


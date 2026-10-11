import requests,json, html,re
from config import NASA_API_KEY
from datetime import datetime
from zoneinfo import ZoneInfo

# print(NASA_API_KEY)

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
    html_text = re.sub(
    r'<a\s+[^>]*href="([^"]+)"[^>]*>(.*?)</a>',
    r"[\2](\1)",
    html_text,
    flags=re.S,
    )
    html_text = re.sub(r"<[^>]+>", "", html_text)
    return html.unescape(html_text).strip()

#gets the date in the eastern timezone in the correct format
#this is becauase nasa's api update at midnight eastern time. therfore if your timezone is different this needs to be accounted for
def nasa_date():
    return datetime.now(ZoneInfo("America/New_York")).strftime("%Y-%m-%d")

# Astrophotography of the day API endpoint
# GET https://science.nasa.gov/wp-json/wp/v2/apod-basic
def APOD_API_request():
    url = "https://science.nasa.gov/wp-json/wp/v2/apod-basic"
    params = {
        "api_key": NASA_API_KEY,
        "date": nasa_date(),
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
        "explanation": strip_html(entry["explanation"]),
        "credit": strip_html_convert_links(entry["credit"]),
        "image_url": entry.get("hdurl"),
        "page_url": entry["permalink"],
        "hdurl": entry.get("hdurl", ""),
        "alt": entry.get("alt", ""),
        "media_type": entry["media_type"],
    }

# test because it will only run if the file is run directly
if __name__ == "__main__":
    apod_data = APOD_API_request()
    if apod_data:
        print(json.dumps(apod_data, indent=2, ensure_ascii=False)[:2000])
#        print(apod_data)


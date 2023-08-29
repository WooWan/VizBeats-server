import re
import googleapiclient.discovery
import googleapiclient.errors
from youtube_title_parse import get_artist_title
from yt_dlp import YoutubeDL
import subprocess

def perform_search(query: str):
    api_service_name = "youtube"
    api_version = "v3"

    youtube = googleapiclient.discovery.build(
        api_service_name,
        api_version,
        developerKey=YOUTUBE_API_KEY,
        cache_discovery=False
    )

    search_request = youtube.search().list(part="snippet", maxResults=10, q=query)
    search_result = search_request.execute()
    search_items = search_result['items']

    ids = [
        item['id']['videoId'] for item in search_items
        if item['id']['kind'] == 'youtube#video'
           and item['snippet']['liveBroadcastContent'] == 'none'
    ]

    duration_request = youtube.videos().list(part='contentDetails', id=','.join(ids))
    duration_result = duration_request.execute()
    duration_items = duration_result['items']
    duration_dict = {
        item['id']: item['contentDetails']['duration']
        for item in duration_items
    }

    videos = []
    for item in search_items:
        if item['id']['kind'] == 'youtube#video' and item['snippet']['liveBroadcastContent'] == 'none' and item['id'][
            'videoId'] in duration_dict:
            parsed_artist = None
            parsed_title = None
            result = get_artist_title(item['snippet']['title'])

            if result:
                parsed_artist, parsed_title = result
            else:
                parsed_artist = item['snippet']['channelTitle']
                parsed_title = item['snippet']['title']

            duration = duration_dict[item['id']['videoId']]
            if (parse_duration(duration) < 60 * 10):
                videos.append({
                    'id': item['id']['videoId'],
                    'title': item['snippet']['title'],
                    'parsed_artist': parsed_artist,
                    'parsed_title': parsed_title,
                    'channel': item['snippet']['channelTitle'],
                    'thumbnail': item['snippet']['thumbnails']['default']['url'],
                    'duration': duration_dict[item['id']['videoId']],
                })
    return videos
def parse_duration(duration):
    pattern = r'P(?:T(?:([0-9]+)H)?(?:([0-9]+)M)?(?:([0-9]+)S)?)?'
    match = re.match(pattern, duration)

    if not match:
        return None

    hours = int(match.group(1)) if match.group(1) else 0
    minutes = int(match.group(2)) if match.group(2) else 0
    seconds = int(match.group(3)) if match.group(3) else 0

    total_seconds = hours * 3600 + minutes * 60 + seconds
    return total_seconds

def download_from_url(url, dir_path):
    opts = {
        'format': 'bestaudio/best',
        'forcefilename': True,
        'outtmpl': dir_path,
        'cachedir': False,
        'noplaylist': True
    }
    with YoutubeDL(opts) as ydl:
        ydl.download([url])

def webm_to_mp3(webm_path, mp3_path):
    cmds = ['ffmpeg', '-i', webm_path, '-vn', '-ab', '192K', '-y', mp3_path]
    subprocess.Popen(cmds)
    print('Converting', webm_path, 'to', mp3_path)
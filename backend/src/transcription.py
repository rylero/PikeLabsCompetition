from youtube_transcript_api import YouTubeTranscriptApi

def get_transcription(url):
    video_id = url.split("v=")[1].split("&")[0]
    captions = YouTubeTranscriptApi.get_transcript(video_id, languages=["en"])
    transcript = ""
    for caption in captions:
        transcript += caption["text"] + " "
    return transcript
import pytube
from moviepy.editor import *
from django.http import HttpResponseBadRequest
import openai
import environ
from .models import Snippet, YoutubeVideo

env = environ.Env()
# reading .env file
environ.Env.read_env()

openai.api_key = env("OPENAI_API_KEY")


def create_text_snippet(video_id, snippet_start, snippet_end, user):
    url = f'https://www.youtube.com/watch?v={video_id}'

    # Download video and convert to mp3 file
    try:
        # Download the video using pytube
        video = pytube.YouTube(url)
        stream = video.streams.filter(only_audio=True).first()
        stream.download()

        # Convert the video to MP3
        video_path = stream.default_filename
        audio = AudioFileClip(video_path)

        # Extract the snippet audio:
        clipped_audio = audio.subclip(snippet_start, snippet_end)
        audio_path = video_path[:-4] + ".mp3"
        clipped_audio.write_audiofile(audio_path)

        print("The video has been converted to MP3 successfully")
    except Exception as e:
        return HttpResponseBadRequest("Error downloading audio file: " + str(e))
    
    # Transcribe snippet audio
    try:
        audio_file = open(audio_path, "rb")
        transcript = openai.Audio.transcribe("whisper-1", audio_file)
    except Exception as e:
        return HttpResponseBadRequest("Error transcribing audio file: " + str(e))
    
    youtube_video, created = YoutubeVideo.objects.get_or_create(
        title=video.title,
        video_id=video_id,
        url=url,
    )

    snippet = Snippet.objects.create(
            text=transcript["text"],
            video=youtube_video,
            start=snippet_start,
            end=snippet_end,
            owner=user
        )

    # Close the audio objects
    audio.close()
    audio_file.close()
    # Delete the files from the server
    os.remove(audio_path)
    os.remove(video_path)

    return snippet

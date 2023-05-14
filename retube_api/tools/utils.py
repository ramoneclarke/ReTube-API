import math
import pytube
from moviepy.editor import *
from django.http import HttpResponseBadRequest
import openai
import environ
import tiktoken
from .models import Snippet, YoutubeVideo, Summary

env = environ.Env()
environ.Env.read_env()

openai.api_key = env("OPENAI_API_KEY")


def calculate_tokens_from_string(text):
    """Returns the number of tokens in a text string."""
    encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
    num_tokens = len(encoding.encode(text))
    return num_tokens


def split_transcript_to_chunks(text, num_chunks):
    """Returns a list of chunks of text"""
    print("Splitting transcript into chunks")
    sentences = text.split(".")
    chunks = []
    current_chunk = ""
    for sentence in sentences:
        current_chunk += sentence + "."
        if len(current_chunk) > len(text) // num_chunks:
            chunks.append(current_chunk)
            current_chunk = ""
    if current_chunk:
        chunks.append(current_chunk)

    return chunks


def summarise_youtube_video(text):
    """Returns a summary of a youtube video transcript"""
    print("Summarising video")
    num_tokens = calculate_tokens_from_string(text)
    # text in system and final user content = 44 tokens
    max_tokens = 4096 - 44 - num_tokens
    summary = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": "You are a concise and informative speaker. You're going to summarise this youtube video, from its transcript",
            },
            {"role": "user", "content": text},
            {
                "role": "user",
                "content": "Write a set of bullet points explaining the key concepts and topics of the video. keep it concise. just summarise",
            },
        ],
        max_tokens=max_tokens - 100,
    )
    return summary["choices"][0]["message"]["content"]


def summarise_text_chunk(text):
    """Returns a summary of a chunk of text from a long youtube transcript"""
    print("Summarising text chunk")
    num_tokens = calculate_tokens_from_string(text)
    # text in system and final user content = 49 tokens
    max_tokens = 4096 - 49 - num_tokens
    summary = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": "You are a concise and informative speaker. You're going to summarise this part of the youtube video, from its transcript",
            },
            {"role": "user", "content": text},
            {
                "role": "user",
                "content": "Write a set of bullet points explaining the key concepts and topics of this chunk of the video transcript. keep it very concise, max 3 bullets. just summarise",
            },
        ],
        max_tokens=400,
    )
    return summary["choices"][0]["message"]["content"]


def summarise_summaries(summaries_list):
    """Returns a summary of multiple summary chunks for a youtube video"""
    print("Summarising summaries")
    text = ""
    for i, summary in enumerate(summaries_list):
        text += summary
        if i < len(summaries_list) - 1:
            text += "\n"  # add a \n between summaries

    num_tokens = calculate_tokens_from_string(text)
    # text in system and final user content = 52 tokens
    max_tokens = 4096 - 53 - num_tokens
    summary = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": "You are a concise and informative speaker. You're going to summarise this video, from this string of summaries for the video",
            },
            {"role": "user", "content": text},
            {
                "role": "user",
                "content": "Write a set of bullet points explaining the key concepts and topics of this video. keep it very concise. just summarise",
            },
        ],
        max_tokens=max_tokens - 100,
    )
    return summary["choices"][0]["message"]["content"]


def create_text_snippet(video_id, snippet_start, snippet_end, user):
    """Transcribes a video snippet and returns the Snippet object"""
    url = f"https://www.youtube.com/watch?v={video_id}"

    # Download video and convert to mp3 file
    try:
        try_again = True
        counter = 0
        while try_again:
            try:
                # Download the video using pytube
                video = pytube.YouTube(url, use_oauth=True, allow_oauth_cache=True)
                print(video)
                stream = video.streams.filter(only_audio=True).first()
                print(stream)
                stream.download()
                print("Downloaded video")
                try_again = False
            except Exception as e:
                if counter > 4:
                    return HttpResponseBadRequest(
                        "Error downloading audio file: " + str(e)
                    )
                counter += 1
                print(f"Download video attempt #{counter}")

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
        length=video.length,
        url=url,
    )

    snippet = Snippet.objects.create(
        text=transcript["text"],
        video=youtube_video,
        start=snippet_start,
        end=snippet_end,
        owner=user,
    )

    # Close the audio objects
    audio.close()
    audio_file.close()
    # Delete the files from the server
    os.remove(audio_path)
    os.remove(video_path)

    return snippet


def create_summary_using_max_tokens_per_chunk(video_id, user):
    """Returns a text summary of a youtube video"""

    url = f"https://www.youtube.com/watch?v={video_id}"

    # Download video and convert to mp3 file
    try:
        # Download the video using pytube
        video = pytube.YouTube(url, use_oauth=True, allow_oauth_cache=True)
        stream = video.streams.filter(only_audio=True).first()
        stream.download()

        # Convert the video to MP3
        video_path = stream.default_filename
        audio = AudioFileClip(video_path)

        # Extract the audio:
        audio_path = video_path[:-4] + ".mp3"

        # Split audio into 10-minute chunks if it's longer than 10 minutes
        audio_duration = audio.duration
        if audio_duration > 600:
            num_chunks = int(math.ceil(audio_duration / 600))
            for i in range(num_chunks):
                start_time = i * 600
                end_time = min((i + 1) * 600, audio_duration)
                chunk_path = audio_path[:-4] + f"_{i}.mp3"
                chunk = audio.subclip(start_time, end_time)
                chunk.write_audiofile(chunk_path)
        else:
            audio.write_audiofile(audio_path)

        print("The video has been converted to MP3 successfully")
    except Exception as e:
        return HttpResponseBadRequest("Error downloading audio file: " + str(e))

    # Transcribe audio
    print("Transcribing audio")
    try:
        chunk_paths = []
        if audio_duration > 600:
            transcript = ""
            for i in range(num_chunks):
                chunk_path = audio_path[:-4] + f"_{i}.mp3"
                chunk_paths.append(chunk_path)
                with open(chunk_path, "rb") as f:
                    chunk_transcript = openai.Audio.transcribe("whisper-1", f)
                    transcript += chunk_transcript["text"]
                    if i < num_chunks - 1:
                        transcript += " "  # add a space between chunks
        else:
            with open(audio_path, "rb") as f:
                transcript = openai.Audio.transcribe("whisper-1", f)
                transcript = transcript["text"]
    except Exception as e:
        return HttpResponseBadRequest("Error transcribing audio file: " + str(e))

    youtube_video, created = YoutubeVideo.objects.get_or_create(
        title=video.title,
        video_id=video_id,
        length=video.length,
        url=url,
    )

    # Create summary
    print("Creating summary")
    num_tokens = calculate_tokens_from_string(transcript)
    max_tokens_per_chunk = 2000
    if num_tokens > (3000):
        # Split transcript into chunks
        num_of_chunks = int(math.ceil(num_tokens / max_tokens_per_chunk))
        chunks = split_transcript_to_chunks(transcript, num_of_chunks)

        # Summarise chunks
        summaries = []
        for chunk in chunks:
            summary = summarise_text_chunk(chunk)
            summaries.append(summary)

        # Create the final summary from all the summaries
        video_summary = summarise_summaries(summaries)
    else:
        # create one summary
        video_summary = summarise_youtube_video(transcript)

    summary = Summary.objects.create(
        bullet_points=video_summary, video=youtube_video, owner=user
    )

    # Close the audio objects
    audio.close()
    # Delete the files from the server
    if os.path.exists(audio_path):
        os.remove(audio_path)
    for path in chunk_paths:
        os.remove(path)
    os.remove(video_path)

    return summary


def create_summary(video_id, user):
    """Returns a text summary of a youtube video"""

    url = f"https://www.youtube.com/watch?v={video_id}"

    # Download video and convert to mp3 file
    try:
        # Download the video using pytube
        video = pytube.YouTube(url, use_oauth=True, allow_oauth_cache=True)
        stream = video.streams.filter(only_audio=True).first()
        stream.download()

        # Convert the video to MP3
        video_path = stream.default_filename
        audio = AudioFileClip(video_path)

        # Extract the audio:
        audio_path = video_path[:-4] + ".mp3"

        # Split audio into 10-minute chunks if it's longer than 10 minutes
        audio_duration = audio.duration
        if audio_duration > 600:
            num_chunks = int(math.ceil(audio_duration / 600))
            for i in range(num_chunks):
                start_time = i * 600
                end_time = min((i + 1) * 600, audio_duration)
                chunk_path = audio_path[:-4] + f"_{i}.mp3"
                chunk = audio.subclip(start_time, end_time)
                chunk.write_audiofile(chunk_path)
        else:
            audio.write_audiofile(audio_path)

        print("The video has been converted to MP3")
    except Exception as e:
        return HttpResponseBadRequest("Error downloading audio file: " + str(e))

    # Transcribe audio
    print("Transcribing audio")
    try:
        chunk_paths = []
        chunks_transcripts = []
        if audio_duration > 600:
            transcript = ""
            for i in range(num_chunks):
                chunk_path = audio_path[:-4] + f"_{i}.mp3"
                chunk_paths.append(chunk_path)
                with open(chunk_path, "rb") as f:
                    chunk_transcript = openai.Audio.transcribe("whisper-1", f)
                    chunks_transcripts.append(chunk_transcript["text"])
        else:
            with open(audio_path, "rb") as f:
                transcript = openai.Audio.transcribe("whisper-1", f)
                transcript = transcript["text"]
    except Exception as e:
        return HttpResponseBadRequest("Error transcribing audio file: " + str(e))

    youtube_video, created = YoutubeVideo.objects.get_or_create(
        title=video.title,
        video_id=video_id,
        length=video.length,
        url=url,
    )

    # Create summary
    print("Creating summary")
    if audio_duration > 600:
        # Summarise chunks
        print("Summarising chunks")
        summaries = []
        for chunk in chunks_transcripts:
            summary = summarise_text_chunk(chunk)
            summaries.append(summary)

        # Create the final summary from all the summaries
        video_summary = summarise_summaries(summaries)
    else:
        # create one summary
        video_summary = summarise_youtube_video(transcript)

    summary = Summary.objects.create(
        bullet_points=video_summary, video=youtube_video, owner=user
    )

    # Close the audio objects
    audio.close()
    # Delete the files from the server
    if os.path.exists(audio_path):
        os.remove(audio_path)
    for path in chunk_paths:
        os.remove(path)
    os.remove(video_path)

    return summary

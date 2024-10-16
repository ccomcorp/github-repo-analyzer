import os
import yt_dlp
import whisper
import torch
import openai
from pytube import YouTube
from tqdm import tqdm
import os
import requests
from dotenv import load_dotenv
import datetime
import warnings
import spacy
from typing import List
import openai
import ssl
import time
import threading
import subprocess
import sys

# Load environment variables
load_dotenv()

# Capacities API settings
CAPACITIES_API_KEY = os.getenv('CAPACITIES_API_KEY')
SPACE_ID = os.getenv('SPACE_ID')
BASE_URL = "https://api.capacities.io"

# Validate Capacities API credentials
if not CAPACITIES_API_KEY or not SPACE_ID:
    raise ValueError("CAPACITIES_API_KEY or SPACE_ID not found in environment variables")

# OpenAI API settings
openai.api_key = os.getenv('OPENAI_API_KEY')
if not openai.api_key:
    raise ValueError("OPENAI_API_KEY not found in environment variables")

# Disable SSL verification
ssl._create_default_https_context = ssl._create_unverified_context

# Set the device (GPU if available or CPU)
device = "cuda" if torch.cuda.is_available() else "cpu"

# Load the spacy model
if not spacy.util.is_package("en_core_web_sm"):
    spacy.cli.download("en_core_web_sm")
nlp = spacy.load("en_core_web_sm")

# Load Whisper model
def load_whisper_model():
    model = whisper.load_model("base", device=device)
    return model

whisper_model = load_whisper_model()

def sanitize_filename(title):
    return "".join(c for c in title if c.isalnum() or c in (' ', '_', '-')).rstrip()

def format_timestamp(seconds):
    return str(datetime.timedelta(seconds=int(seconds)))

def extract_chapters(video_url):
    ydl_opts = {
        'quiet': True,
        'skip_download': True,
        'no_warnings': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(video_url, download=False)
            chapters = info.get('chapters', [])
            if not chapters:
                print("No chapters found.")
            return chapters
        except Exception as e:
            print(f"Error extracting video information: {e}")
            return []

def video_to_audio(video_URL, destination, final_filename):
    try:
        ydl_opts_info = {
            'format': 'bestaudio/best',
            'skip_download': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts_info) as ydl:
            info = ydl.extract_info(video_URL, download=False)
            total_bytes = info.get('filesize') or info.get('filesize_approx', 0)
        
        pbar = tqdm(total=total_bytes, unit='B', unit_scale=True, desc="Downloading")

        def progress_hook(d):
            if d['status'] == 'downloading':
                pbar.update(d['downloaded_bytes'] - pbar.n)
            elif d['status'] == 'finished':
                pbar.close()

        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': f'{destination}/{final_filename}.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'progress_hooks': [progress_hook],
            'quiet': True
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_URL])
        return f"{destination}/{final_filename}.mp3", final_filename
    except Exception as e:
        print(f"Error downloading video: {e}")
        return None, None

def transcribe_audio(audio_file):
    try:
        print("Transcribing audio...")
        start_time = time.time()

        # Create an indeterminate progress bar
        pbar = tqdm(total=0, desc="Transcribing", bar_format='{l_bar}{bar}')

        def update_progress():
            while pbar.n == 0:
                pbar.update(0)
                time.sleep(0.1)

        # Start the progress bar update in a separate thread
        progress_thread = threading.Thread(target=update_progress)
        progress_thread.start()

        # Perform transcription
        result = whisper_model.transcribe(audio_file, verbose=False)

        # Stop the progress bar
        pbar.n = 1
        pbar.refresh()
        pbar.close()
        progress_thread.join()

        elapsed_time = int(time.time() - start_time)
        print(f"\nTranscription completed in {elapsed_time} seconds.")
        return result["segments"]
    except Exception as e:
        print(f"Error during transcription: {e}")
        return None

def segment_transcript(transcript, chapters):
    segmented_transcript = []
    for chapter in chapters:
        start_time = chapter['start_time']
        end_time = chapter.get('end_time', float('inf'))
        chapter_text = []
        for segment in transcript:
            if start_time <= segment['start'] < end_time:
                chapter_text.append(segment['text'])
        segmented_transcript.append({
            'title': chapter['title'],
            'start_time': start_time,
            'text': ' '.join(chapter_text)
        })
    return segmented_transcript

import openai

# Set OpenAI API key
openai.api_key = os.getenv('OPENAI_API_KEY')  # Ensure your API key is set correctly

# Example of using the OpenAI API
def generate_tags(chapter_text):
    try:
        prompt = f"""
You are an assistant that extracts key concepts and ideas from text content to generate relevant tags for semantic search.

Please follow these steps:

1. **Writer**: Read the following text carefully and identify the key concepts and ideas. Generate an initial list of tags based on these concepts.

2. **Reviewer**: Review the initial list of tags. Refine them to improve their effectiveness for semantic search by ensuring they are concise, relevant, and free of duplicates.

3. **Final Output**: Provide only the final set of up to 5 refined tags, separated by commas.

---

**Text**:

{chapter_text}

---

**Final Tags**:
"""
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=100,
            temperature=0.3
        )
        # Debugging: Print the raw response from OpenAI
        print("OpenAI Response:", response.choices[0].message.content)
        
        tags = response.choices[0].message.content.strip().split(',')
        return [tag.strip() for tag in tags if tag.strip()]
    except Exception as e:
        print(f"Error generating tags: {e}")
        return []

def create_weblink_in_capacities(url, title, transcript, tags):
    headers = {
        "Authorization": f"Bearer {CAPACITIES_API_KEY}",
        "Content-Type": "application/json",
        "accept": "application/json"
    }
    
    print("Headers:", headers)  # Debugging line
    
    # Limit tags to 30
    limited_tags = tags[:30] if len(tags) > 30 else tags
    
    data = {
        "spaceId": SPACE_ID,
        "url": url,
        "titleOverwrite": title,
        "descriptionOverwrite": "YouTube video transcript with AI-generated tags",
        "tags": limited_tags,
        "mdText": transcript
    }
    
    response = requests.post(f"{BASE_URL}/save-weblink", headers=headers, json=data)
    
    if response.status_code == 200:
        print("Successfully created WebLink in Capacities")
        print(f"Tags added to Capacities object: {', '.join(limited_tags)}")
        return response.json()
    else:
        print(f"Failed to create WebLink in Capacities. Status code: {response.status_code}")
        print(f"Response: {response.text}")
        return None

def get_video_info(url):
    url = url.strip().strip('`')
    try:
        ydl_opts = {'quiet': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return info
    except Exception as e:
        print(f"Error extracting video information: {str(e)}")
        return None

# Get the directory of the current script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Reference the "T1" folder in the same directory as the script
t1_folder_path = os.path.join(script_dir, "T1")

# Ensure the "T1" folder exists
if not os.path.exists(t1_folder_path):
    os.makedirs(t1_folder_path)

def process_video(video_url):
    # Use the t1_folder_path as the destination
    destination = t1_folder_path

    # Get video info
    video_info = get_video_info(video_url)

    if video_info:
        video_title = video_info.get('title', 'Unknown Title')
        print(f"Video title: {video_title}")
        final_filename = sanitize_filename(video_title)
    else:
        print("Failed to fetch video information.")
        return

    audio_file_path = os.path.join(destination, f"{final_filename}.mp3")
    transcript_filename = os.path.join(destination, f"{final_filename}_transcript.txt")

    print("Extracting chapters...")
    chapters = extract_chapters(video_url)
    
    if not chapters:
        print("No chapters found. Processing video with 1chex.py...")
        subprocess.call([sys.executable, '1chex.py', video_url])
        return
    else:
        print(f"Number of chapters extracted: {len(chapters)}")
        print("Processing video with chapters...")
        if os.path.exists(audio_file_path) and os.path.exists(transcript_filename):
            print("Audio file and transcript already exist. Loading existing transcript.")
            with open(transcript_filename, 'r', encoding='utf-8') as f:
                capacities_transcript = f.read()
            
            # Extract tags from the existing transcript
            all_tags = set()
            for line in capacities_transcript.split('\n'):
                if line.startswith('**Tags:**'):
                    chapter_tags = [tag.strip() for tag in line.replace('**Tags:**', '').split(',')]
                    all_tags.update(chapter_tags)
        else:
            print("Downloading video and converting to audio...")
            audio_file_path, _ = video_to_audio(video_url, destination, final_filename)

            if audio_file_path:
                print(f"Audio saved as {audio_file_path}")
                
                transcript = transcribe_audio(audio_file_path)
                
                if transcript:
                    print(f"Number of transcribed segments: {len(transcript)}")
                    
                    print("Segmenting transcript into chapters...")
                    segmented_transcript = segment_transcript(transcript, chapters)
                    
                    capacities_transcript = f"# Transcript\n\nVideo URL: {video_url}\n\n"
                    all_tags = set()
                    for chapter in segmented_transcript:
                        formatted_time = format_timestamp(chapter['start_time'])
                        print(f"Generating tags for chapter: {chapter['title']}")
                        chapter_tags = generate_tags(chapter['text'])
                        all_tags.update(chapter_tags)
                        
                        capacities_transcript += f"## {chapter['title']}\n"
                        capacities_transcript += f"Start Time: {formatted_time}\n"
                        capacities_transcript += f"{chapter['text']}\n"
                        capacities_transcript += f"**Tags:** {', '.join(chapter_tags)}\n\n"
                    
                    capacities_transcript += f"\n## All Tags\n{', '.join(all_tags)}\n"

                    with open(transcript_filename, 'w', encoding='utf-8') as f:
                        f.write(capacities_transcript)

                    print(f"\nSegmented transcript saved to {transcript_filename}")
                else:
                    print("Failed to transcribe the audio.")
                    return
            else:
                print("Failed to download and process the video.")
                return

        # Create WebLink in Capacities
        print("Creating WebLink in Capacities...")
        result = create_weblink_in_capacities(video_url, video_title, capacities_transcript, list(all_tags))

        if result:
            print("WebLink created successfully in Capacities.")
        else:
            print("Failed to create WebLink in Capacities.")

# Main execution loop
if __name__ == "__main__":
    while True:
        video_url = input("Enter the YouTube video URL (or 'quit' to exit): ")
        if video_url.lower() == 'quit':
            print("Exiting the program. Goodbye!")
            break
        process_video(video_url)
        print("\n")

# Get the directory of the current script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Reference the "T1" folder in the same directory as the script
t1_folder_path = os.path.join(script_dir, "T1")

# Ensure the "T1" folder exists
if not os.path.exists(t1_folder_path):
    os.makedirs(t1_folder_path)

# Now you can use t1_folder_path to save files
audio_file_path = os.path.join(t1_folder_path, "audio.mp3")
transcript_file_path = os.path.join(t1_folder_path, "transcript.txt")

# Example usage
print(f"Audio file will be saved to: {audio_file_path}")
print(f"Transcript file will be saved to: {transcript_file_path}")
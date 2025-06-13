import whisper
import ffmpeg
import os
import re
import math
from datetime import timedelta
import xml.etree.ElementTree as ET

# User configurable
M4A_FILE = "./audios/esoteric.m4a"
OUTPUT_FCPXML = "subtitles.fcpxml"
MAX_WORDS_PER_SUBTITLE = 4
FRAMERATE = 30

# Load Whisper model
model = whisper.load_model("base")

# Transcribe
print("Transcribing...")
result = model.transcribe(M4A_FILE)

# Split segments into subtitles of N words max
def split_into_subtitles(segments, max_words):
    subtitles = []
    for seg in segments:
        words = seg['text'].strip().split()
        num_splits = math.ceil(len(words) / max_words)
        for i in range(num_splits):
            chunk = words[i*max_words:(i+1)*max_words]
            start = seg['start'] + (i * (seg['end'] - seg['start']) / num_splits)
            end = seg['start'] + ((i+1) * (seg['end'] - seg['start']) / num_splits)
            subtitles.append({
                'start': start,
                'end': end,
                'text': ' '.join(chunk)
            })
    return subtitles

subtitles = split_into_subtitles(result['segments'], MAX_WORDS_PER_SUBTITLE)

# Create FCPXML
def seconds_to_timecode(seconds, framerate):
    frames = int((seconds - int(seconds)) * framerate)
    td = timedelta(seconds=int(seconds))
    hours, remainder = divmod(td.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02}:{minutes:02}:{seconds:02}:{frames:02}"

def create_fcpxml(subtitles, framerate, output_file):
    fcpxml = ET.Element("fcpxml", version="1.8")
    
    resources = ET.SubElement(fcpxml, "resources")
    ET.SubElement(resources, "format", id="r1", name="FFVideoFormat1080p30", frameDuration=f"100/{framerate*100}s")
    ET.SubElement(resources, "effect", id="r2", name="Basic Title", uid=".../Basic Title")
    
    library = ET.SubElement(fcpxml, "library")
    event = ET.SubElement(library, "event", name="Subtitles")
    project = ET.SubElement(event, "project", name="Subtitles Project")
    sequence = ET.SubElement(project, "sequence", duration="600s", format="r1")
    spine = ET.SubElement(sequence, "spine")

    for idx, sub in enumerate(subtitles):
        duration_frames = int((sub['end'] - sub['start']) * framerate)
        start_frames = int(sub['start'] * framerate)
        duration = f"{duration_frames}/{framerate}s"
        offset = f"{start_frames}/{framerate}s"

        title = ET.SubElement(
            spine, 
            "title", 
            name="Subtitle", 
            lane="1", 
            offset=offset, 
            duration=duration, 
            start=offset, 
            role="title", 
            ref="r2"  # <<<<<< IMPORTANT: the ref attribute
        )
        text_elem = ET.SubElement(title, "text")
        ET.SubElement(text_elem, "text-style").text = sub['text']

    tree = ET.ElementTree(fcpxml)
    ET.indent(tree, space="  ", level=0)
    tree.write(output_file, encoding="utf-8", xml_declaration=True)

# Generate FCPXML
print("Generating FCPXML...")
create_fcpxml(subtitles, FRAMERATE, OUTPUT_FCPXML)
print(f"Done. FCPXML saved as {OUTPUT_FCPXML}")

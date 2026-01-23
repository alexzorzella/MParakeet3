import os
import yt_dlp
import argparse
import time

from pathlib import Path

def download_playlist():
    parser = argparse.ArgumentParser()
    parser.add_argument("-l", "--link", type=str, help="Playlist link. Required")
    parser.add_argument("-o", "--output", type=str, help="Output directory. Required")
    parser.add_argument("-f", "--filetype", type=str, help="The format of the output files. Default: mp3")
    parser.add_argument("-q", "--quiet", type=bool, help="Whether the downloader doesn't print logs. Default: True")

    args = parser.parse_args()

    link = args.link
    output_directory = args.output
    filetype = args.filetype
    quiet = args.quiet

    while link is None:
        link = input("Playlist link: ")

    while output_directory is None:
        output_directory = input("Output directory: ").strip('"')

    if filetype is None:
        filetype = "mp3"

    if quiet is None:
        quiet = True

    if Path(output_directory).is_dir():
        deletion_confirmation = input(f"The directory {output_directory} already exists. Music already present there will be skipped. Continue? (y/n): ")

        if deletion_confirmation.lower() != "y":
            return

    ydl_opts = {
        "format": "bestaudio/best",
        "extractaudio": True,
        "audioformat": filetype,
        "outtmpl": os.path.join(output_directory, "%(title)s.%(ext)s"),
        "noplaylist": False,
        "quiet": quiet,
        "no_warnings": quiet,
        "download_archive": "downloaded.txt",
        "progress_hooks": [hook],
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": filetype,
            "preferredquality": "192"
        }]
    }

    queue_download(link, ydl_opts)

def queue_download(link: str, ydl_opts: dict, sleep_for: int = 1):
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                ydl.download([link])
            except:
                print(f"Process most likely rate limited, trying again in {int(sleep_for)} second(s).")

                time.sleep(sleep_for)
                queue_download(link, ydl_opts, sleep_for * 2)

                return
        print(f"Successfully downloaded {link}")
    except Exception as e:
        print(f"An error occurred while trying to download the playlist: {e}")

def hook(d):
    if d["status"] == "finished":
        filename = Path(d["filename"]).stem
        print(f" Downloaded {filename}")

if __name__ == '__main__':
    download_playlist()
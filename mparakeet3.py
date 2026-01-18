import re
import shutil
import itertools
import subprocess
from pathlib import Path
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed

from tqdm import tqdm

from jobdata import JobData
from sconfig import parse_config

def convert_and_partition():
    config_variables = parse_config(section="music", params=[("source", str), ("output", str), ("maxthreads", int), ("foldertracklimit", int)])
    source, destination, max_threads, folder_track_limit = config_variables["source"], config_variables["output"], config_variables["maxthreads"], config_variables["foldertracklimit"]

    destination = Path(destination)

    if destination.exists() and destination.is_dir():
        delete_directory = input(f"A folder already exists at {destination}.\n"
                                 f"Type 'yes' to delete the directory and continue: ")

        if delete_directory != "yes":
            return

        shutil.rmtree(destination)

    destination.mkdir(parents=True, exist_ok=True)

    source_folder = Path(source)
    extensions = frozenset([ ".m4a", ".opus", ".mp3", ".flac", ".wav" ])

    audio_files = [ f for f in source_folder.rglob("*") if f.suffix.lower() in extensions ]

    folder_track_map = defaultdict(list)

    for file in audio_files:
        source_folder = file.parent
        filename = file.name

        folder_track_map[source_folder].append(filename)

        # logger.info(file)

    folder_track_map_partitioned = defaultdict(list)

    for source_folder, songs in folder_track_map.items():
        folder_track_map_partitioned[source_folder] = list(itertools.batched(songs, folder_track_limit))

        # logger.info(f"{source_folder}: {len(songs)} songs")

    job_datas = []

    for source_folder, batched in folder_track_map_partitioned.items():
        if len(batched) == 1:
            job_datas.extend([JobData(source_path=source_folder / track, destination_path=(destination / source_folder.name / track).with_suffix(".mp3")) for track in batched[0]])
        else:
            for index, batch in enumerate(batched):
                first_track = index * folder_track_limit
                last_track = min((index + 1) * folder_track_limit, sum(map(len, batched)))

                job_datas.extend([JobData(source_path=source_folder / track,
                                          destination_path=(destination / f"{source_folder.name} ({first_track+1}-{last_track})" / track).with_suffix(".mp3")) for track in
                                  batch])

    # for job_datum in job_datas:
    #     logger.info(job_datum)

    with ThreadPoolExecutor(max_workers=max_threads) as executor:
        futures = [executor.submit(run_ffmpeg, job_data) for job_data in job_datas]
        for f in tqdm(as_completed(futures), total=len(futures), desc="Processing files", unit="file", ncols=100):
            result = f.result()

    print(f"Converted {len(audio_files)} audio files!")

    # logger.info(f"Found {len(audio_files)} files")

def run_ffmpeg(job_data: JobData):
    job_data.destination_path.parent.mkdir(parents=True, exist_ok=True)

    clean_title = re.sub(r"\s\([a-z0-9]+_(?:Opus|AAC)\)$", '', job_data.source_path.stem)

    command = [
        "ffmpeg",
        "-loglevel", "error",
        "-i", str(job_data.source_path),
        "-codec:a", "libmp3lame",
        "-q:a", "0",
        "-map_metadata", "0",
        "-metadata", f"title={clean_title}",
        "-id3v2_version", "3",
        "-y",
        str(job_data.destination_path)
    ]
    subprocess.run(command, shell=True)

if __name__ == "__main__":
    convert_and_partition()
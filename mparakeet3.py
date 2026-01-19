import shutil
import argparse
import itertools
from pathlib import Path
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed

from tqdm import tqdm

from jobdata import JobData
from sconfig import parse_config_with_defaults
from ffmparakeet import run_ffmpeg

def convert_and_partition():
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--source", type=str, help="Music directory")
    parser.add_argument("-o", "--output", type=str, help="Output directory")
    parser.add_argument("-t", "--max-threads", type=str, help="The number of CPUs to use")
    parser.add_argument("-l", "--folder-track-limit", type=str, help="The maximum number of tracks per folder")

    args = parser.parse_args()

    config_variables = (
        parse_config_with_defaults(section="music", params=[("source", str, args.source), ("output", str, args.output), ("maxthreads", int, args.max_threads), ("foldertracklimit", int, args.folder_track_limit)]))
    source, destination, max_threads, folder_track_limit = config_variables["source"], config_variables["output"], config_variables["maxthreads"], config_variables["foldertracklimit"]

    if max_threads is None:
        max_threads = 4

    unlimited_track_count = 100_000

    if folder_track_limit is None:
        folder_track_limit = unlimited_track_count

    folder_track_limit_info = f"a {folder_track_limit}" if folder_track_limit < unlimited_track_count else "an unlimited"

    ok = input(f"Copying and converting music from {source} to {destination} using {max_threads} threads with {folder_track_limit_info} track limit per folder. OK? (y/n): ")

    if ok.lower() != "y":
        return

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

    folder_track_map_partitioned = defaultdict(list)

    for source_folder, songs in folder_track_map.items():
        folder_track_map_partitioned[source_folder] = list(itertools.batched(songs, folder_track_limit))

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

    with ThreadPoolExecutor(max_workers=max_threads) as executor:
        futures = [executor.submit(run_ffmpeg, job_data.source_path, job_data.destination_path) for job_data in job_datas]
        for f in tqdm(as_completed(futures), total=len(futures), desc="Processing files", unit="file", ncols=100):
            result = f.result()

    print(f"Converted {len(audio_files)} audio files!")

    # logger.info(f"Found {len(audio_files)} files")

if __name__ == "__main__":
    convert_and_partition()
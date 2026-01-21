import shutil
import argparse
import itertools
from pathlib import Path
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed

from tqdm import tqdm

from jobdata import JobData
from sconfig import parse_config_with_defaults
from ffmparakeet import run_ffmpeg, ffmpeg_encoders

def convert_and_partition():
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--source", type=str, help="Music directory")
    parser.add_argument("-o", "--output", type=str, help="Output directory")
    parser.add_argument("-t", "--max-threads", type=str, help="The number of CPUs to use")
    parser.add_argument("-l", "--folder-track-limit", type=str, help="The maximum number of tracks per folder")
    parser.add_argument("-f", "--filetype", type=str, help="Output file type: i.e. mp3, aac, m4a, flac, wav, ogg")

    args = parser.parse_args()

    source = args.source
    output = args.output

    default_max_threads = 1
    max_threads = default_max_threads if args.max_threads is None else args.max_threads

    def_folder_track_limit = 100_000
    folder_track_limit = def_folder_track_limit if args.folder_track_limit is None else args.folder_track_limit

    default_filetype = "mp3"
    filetype = default_filetype if args.filetype is None else args.filetype

    config_variables = (
        parse_config_with_defaults(
            section="music",
            params=[
                ("source", str, source),
                ("output", str, output),
                ("maxthreads", int, max_threads),
                ("foldertracklimit", int, folder_track_limit),
                ("filetype", str, filetype)]))

    source, destination, max_threads, folder_track_limit, filetype = (
        config_variables["source"],
        config_variables["output"],
        config_variables["maxthreads"],
        config_variables["foldertracklimit"],
        config_variables["filetype"])

    while source is None or not Path(source).is_dir():
        source = input("Source directory: ").strip('"')

    while destination is None:
        destination = input("Output directory: ").strip('"')

    encoder = ffmpeg_encoders[filetype.strip().lower()]

    folder_track_limit_info = f"a {folder_track_limit}" if folder_track_limit < def_folder_track_limit else "an unlimited"

    ok = input(f"Copying and converting music from {source} to {destination} using {max_threads} thread(s) with a {folder_track_limit_info} track limit per folder. OK? (y/n): ")

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

    audio_files = [ f for f in source_folder.rglob("*") if f.suffix.lower()[1:] in ffmpeg_encoders.keys() ]

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
            job_datas.extend([JobData(source_path=source_folder / track, destination_path=(destination / source_folder.name / track).with_suffix(f".{filetype}")) for track in batched[0]])
        else:
            for index, batch in enumerate(batched):
                first_track = index * folder_track_limit
                last_track = min((index + 1) * folder_track_limit, sum(map(len, batched)))

                job_datas.extend([JobData(source_path=source_folder / track,
                                          destination_path=(destination / f"{source_folder.name} ({first_track+1}-{last_track})" / track).with_suffix(f".{filetype}")) for track in
                                  batch])

    with ThreadPoolExecutor(max_workers=max_threads) as executor:
        futures = [executor.submit(run_ffmpeg, job_data.source_path, job_data.destination_path, encoder, True) for job_data in job_datas]
        for f in tqdm(as_completed(futures), total=len(futures), desc="Processing files", unit="file", ncols=100):
            result = f.result()

    print(f"Converted {len(audio_files)} audio files!")

    # logger.info(f"Found {len(audio_files)} files")

if __name__ == "__main__":
    convert_and_partition()
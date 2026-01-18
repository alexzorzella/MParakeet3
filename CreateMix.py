import configparser
import logging.config
import re
import subprocess
import time
from collections import defaultdict
from pathlib import Path
import pathvalidate
from pyfzf.pyfzf import FzfPrompt
from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MP3

config_filename = "config.ini"

logging.config.dictConfig(
    {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "simple": {
                "format": "[%(asctime)s .%(msecs)03d|%(levelname)s|%(name)s|%(filename)s:%(lineno)d] %(message)s",
                "datefmt": "%Y-%m-%dT%H:%M:%S%z",
            }
        },
        "handlers": {
            "stdout": {
                "class": "logging.StreamHandler",
                "formatter": "simple",
                "stream": "ext://sys.stdout",
                # "level": "WARNING",
                # "level": "INFO",
                "level": "DEBUG",
            },
        },
        "loggers": {
            "root": {
                "level": "DEBUG",
                "handlers": [
                    "stdout",
                ],
            }
        },
    }
)

logger = logging.getLogger("createmix")


def get_config_param(config_section, cast_to, param_name):
    try:
        return cast_to(config_section[param_name])
    except:
        error = f"{param_name} not found in {config_filename}."
        logger.exception(error)

        return None


def parse_config():
    config = configparser.ConfigParser()

    config_path = Path(config_filename)

    if not config_path.is_file():
        error = f"{config_filename} not found. Please create a config file."

        logger.error(error)
        raise (FileNotFoundError(error))
    else:
        config.read(config_filename)

        try:
            import_section = config["mix"]
        except:
            return

        search = get_config_param(config_section=import_section, cast_to=str, param_name="search")
        mixout = get_config_param(config_section=import_section, cast_to=str, param_name="mixout")

        return search, mixout


def run_ffmpeg(track_num: int, mix_title: str, input_path: Path, output_path: Path):
    command = [
        "ffmpeg",
        "-loglevel", "error",
        "-i", str(input_path),
        "-c", "copy",
        "-map_metadata", "0",
        "-metadata", f"track={track_num}",
        "-metadata", f"album={mix_title}",
        "-id3v2_version", "3",
        str(output_path),

    ]
    subprocess.run(command, shell=True)

def main():
    search, mixout = parse_config()
    search = Path(search)
    mixout = Path(mixout)

    if not search.exists() or not search.is_dir():
        logger.error(f"Search directory does not exist: {search}")
        return

    mixout.mkdir(parents=True, exist_ok=True)

    mix_title = ""
    while mix_title.strip() == "":
        inp = input("Enter mix title :3 : ")
        mix_title = pathvalidate.sanitize_filename(inp).strip()

    files = list(search.rglob("*.mp3"))

    audio_files = [ MP3(file, ID3=EasyID3) for file in files ]
    file_names = []

    file_name_to_audio_file = defaultdict()

    for audio_file in audio_files:
        track_name = audio_file.get('Title', 'Unknown Title')[0]

        file_names.append(track_name)
        file_name_to_audio_file[track_name] = audio_file

    EXIT = ".exit"
    SHOW = ".show"
    SAVE_AND_CLOSE = ".save"

    options = [*file_names, SHOW, SAVE_AND_CLOSE, EXIT ]
    fzf = FzfPrompt()

    mix = []
    while True:
        selected = fzf.prompt(options)
        if len(selected) != 1:
            continue
        selected = selected[0]

        if selected == SHOW:
            print()

            longest_title = max(len(song.get('Title', 'Unknown Title')[0]) for song in mix) + 10
            total_length: float = 0

            index_format = "00" if len(mix) >= 10 else "0"
            padding = re.sub('.', ' ', f"{len(mix):{index_format}}. ")

            title_a = "Song Title"
            title_b = "Length"
            print(f"{padding}{title_a.ljust(longest_title)} {title_b}")

            for i, song in enumerate(mix):
                song_title = song.get('Title', 'Unknown Title')[0]
                song_length = song.info.length
                time_struct = time.gmtime(song_length)
                song_length_as_str = time.strftime("%M:%S", time_struct)

                total_length += song_length

                print(f"{i+1:{index_format}}. {song_title.ljust(longest_title, '.')} ({song_length_as_str})")

            time_struct = time.gmtime(total_length)
            total_length_as_str = time.strftime("%M:%S", time_struct)

            length_prompt = "Total"
            print(f"{padding}{length_prompt.ljust(longest_title, '.')} ({total_length_as_str})\n")

            input("Press enter to continue...")
            continue
        elif selected == SAVE_AND_CLOSE:
            break
        elif selected == EXIT:
            return

        selected = file_name_to_audio_file[selected]
        mix.append(selected)

    output_mix_path = mixout / mix_title
    output_mix_path.mkdir(parents=True, exist_ok=True)
    for i, file in enumerate(mix):
        filepath = Path(file.filename)
        output_path = output_mix_path / filepath.name
        run_ffmpeg(track_num=i + 1, mix_title=mix_title, input_path=filepath, output_path=output_path)


if __name__ == "__main__":
    main()
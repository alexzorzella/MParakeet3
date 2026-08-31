<div align="center">

[//]: # (<img width="351" height="255" alt="mparakeet3_logo" src="https://github.com/user-attachments/assets/a2a02ff1-5e80-4368-bf8d-861ee0b62990" />)
# MParakeet3

</div>

MParakeet3 is a free, open source mixtape creator that uses mp3 files on your device.

## Requirements
- [ffmpeg](https://www.ffmpeg.org/download.html) (Audio/Video encoder).
- [VLC](https://images.videolan.org/vlc/download-windows.html) (Audio/Video player). Make sure to install the appropriate version for your system. Installing the x32 version on a 64-bit system may cause issues.

To install them on Windows, use `winget install fzf`, `winget install ffmpeg`, and `winget install VideoLAN.VLC`.<br>To install them on Mac, use [Homebrew](https://brew.sh/) to run `brew install fzf`, `brew install ffmpeg`, and `brew install vlc`.

## config.ini
MParakeet3 reads information from a local `config.ini` file if provided one in the same folder as the executable.

```
[theme]
style=windows11

[mix]
search=C:\Users\vkim\Music
mixes=C:\Users\vkim\Music\Mixes
```

### style
Sets the look of the interface. The options may vary from system to system, but on Windows, you may choose from 'windows11', 'fusion', and 'windowsvista'.

### search
Specifies the root folder where your music is stored. You may select tracks from anywhere on your disk while using the application, but issues may arise when trying to load mixes with tracks that aren't present in your root folder. Subfolders are supported.

### mixes
Specifies the root folder where your mixes are saved. Mixes are saved as .txt files. Subfolders are supported.

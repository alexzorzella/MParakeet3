import random

EXAMPLE_ALBUMS = [
    ("Abbey Road", "The Beatles"),
    ("Sgt. Pepper's Lonely Hearts Club Band", "The Beatles"),
    ("The Wall", "Pink Floyd"),
    ("Dark Side of the Moon", "Pink Floyd"),
    ("Feel Special", "Twice"),
    ("Five Miles Out", "Mike Oldfield"),
    ("Tubular Bells", "Mike Oldfield"),
    ("We Like It Here", "Snarky Puppy"),
    ("Minecraft Volume Alpha", "C418"),
    ("Endless Forms Most Beautiful", "Nightwish"),
    ("Merry Christmas", "Mariah Carey"),
    ("Chico Buarque de Hollanda", "Chico Buarque"),
    ("Riot!", "Paramore"),
    ("Color Him Father", "The Winstons"),
    ("Time Out", "The Dave Brubeck Quartet"),
    ("Images and Words", "Dream Theater"),
    ("90125", "Yes"),
    ("2112", "Rush"),
    ("Power Windows", "Rush"),
    ("Signals", "Rush"),
    ("Point of View", "Takanashi Kiara"),
    ("Three Waters and the Check, Please", "Artist"),
    ("Short n' Sweet", "Sabrina Carpenter"),
    ("Hot Pink", "Doja Cat")
]

def get_random_album_and_artist():
    random_entry = EXAMPLE_ALBUMS[random.randint(0, len(EXAMPLE_ALBUMS) - 1)]
    return random_entry[0], random_entry[1]
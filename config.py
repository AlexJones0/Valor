global version
version = "v2.11.10.1"

global DEFAULT_SETTINGS
DEFAULT_SETTINGS = {
    "screen_width": 1920,
    "screen_height": 1080,
    "display_mode": "windowed",
    "window_width": 1280,
    "window_height": 720,
    "fps_limit": 60,
    "font": "nirmalauisemilight",
    "title_font": "verdana",
    "transition_speed": 1,
    "synonym_suggestions_word_depth": 5,
    "tags_shown_per_row": 4,
    "levenshtein_search_threshold": 50,
    "check_synonyms_for_wildcards": True,
    "background_image": None,
    "number_of_category_tags": 3,
    "item_tags_shown_per_row": 3,
    "scroll_speed": 1
}  # default settings used if config.JSON cannot be found

global settings
settings = {}

# imports
from glob import glob as FileTraverse
from json import loads, dumps


def CreateConfig(filepath: str = '') -> dict:
    """ Creates a config.JSON file with default configuration settings. """
    global DEFAULT_SETTINGS
    with open(filepath + 'config.JSON', 'w+') as f:
        f.write(dumps(DEFAULT_SETTINGS))
        f.close()
    import debug
    debug.Log("created new config.JSON file with default settings.")


def AttemptConfigRepair(filepath: str = ''):
    global settings
    global DEFAULT_SETTINGS
    changed_config = []
    for s in DEFAULT_SETTINGS.keys():
        if s not in settings:
            settings[s] = DEFAULT_SETTINGS[s]
            changed_config.append(s)
    if len(changed_config) > 0:
        with open(filepath + 'config.JSON', 'w+') as f:
            f.write(dumps(settings))
            f.close()
        import debug
        debug.Log(
            'Repaired config.JSON file which was missing the following settings: '
            + ', '.join(changed_config))


def ReadConfig(filepath: str = '') -> dict:
    """ Reads configuration settings from the config.JSON file at the specified file path. """
    global settings
    global DEFAULT_SETTINGS
    for file_ in FileTraverse(filepath + 'config.JSON'):
        try:
            with open(file_, 'r') as f:
                contents = f.read()
                if len(contents) == 0:
                    break  # no valid file has been found so create one
                settings = loads(contents)
                f.close()
            AttemptConfigRepair(filepath)
            return
        except:
            import debug
            debug.Log(
                "config.JSON file corrupted; generating new file with default settings."
            )
            break
    # if running below code, no file has been found
    CreateConfig(filepath)
    settings = DEFAULT_SETTINGS.copy()


def SaveConfig(filepath: str = ''):
    """ Saves input settings to the specified config.JSON file, updating the saved configuration settings. """
    global settings
    with open(filepath + 'config.JSON', 'w') as f:
        f.write(dumps(settings))
        f.close()

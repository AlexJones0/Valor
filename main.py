# disable pygame startup prompt
import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = 'hide'

import interaction
import config
import pygame
import debug
import SQL
import encryption
import startup
from controls import controls
from searches import GetTagMostSimilar, SplitByCharacters, FormatImportTags, StrictSearch, WeightedSearch, ExtremeSearch, Operators, FormatResultsToHTML
from vectors import Vector2D
from interface import ScalePosition, Entry, Button, Label, Container, FunctionalEntry, AdvancedLabel, CheckButton, CacheButton, Rectangle
from interface import HoverButton, UnfocusEntry, ConstantFunctionalEntry, RegulatedContainer, ScrollingRegulatedContainer, ImageElement, RatingsBar
from interface import SearchBar
from components import StaticComponent, ScrollComponent
from fnmatch import filter as WildcardMatch
from time import time as CurrentTime
from enum import Enum


class ComponentID(Enum):
    LOADUP = 1
    MAIN = 2
    TAG_LIST = 3
    TAG_FIRST_BAR = 4
    TAG_SECOND_BAR = 5
    TAG_THIRD_BAR = 6
    TAG_FOURTH_BAR = 7
    TAG_FADE_LAYER = 8
    TAG_ADD = 9
    TAG_EDIT = 10
    TAG_CHANGE_EXIT = 11
    TAG_ADD_SUGGESTIONS = 12
    TAG_ADD_SYNONYMS = 13
    ITEM_FIRST_BAR = 14
    ITEM_SECOND_BAR = 15
    ITEM_LIST = 16
    ITEM_ADD = 17
    ITEM_ADD_TAGS = 18
    ITEM_ADD_FADE_LAYER = 19
    SEARCH = 20
    SEARCH_RESULT = 21
    ERROR = 1000  # temp TODO change
    ERROR_FADE_LAYER = 1001  # temp TODO change
    ITEM_ADD_TAGS_ADD = 1002  # temp TODO change
    ITEM_ADD_TAGS_ADD_EXIT = 1003  # temp TODO change
    ITEM_ADD_TAGS_ADD_SUGGESTIONS = 1004  # temp TODO change
    ITEM_ADD_TAGS_ADD_SYNONYMS = 1005  # temp TODO change
    NOTIFICATION = 10000  # temp TODO change


def MakeElementEqualSize(text, font, target_size):
    text_size = Vector2D(font.size(text))
    return (target_size - text_size) / 2


def RemoveStringFromList(data, remove):
    to_remove = []
    for item in data:
        if item == remove:
            to_remove.append(item)
    for item in to_remove:
        data.remove(item)


def CharactersInString(characters, string):
    for character in characters:
        if character in string:
            return True
    return False


class MenuConstructor:
    # a seperate class to avoid the use of mass global variables

    def __init__(self):
        self.font_size = 0.02 * config.settings["window_height"] / 0.6876
        self.standard_ui_font = pygame.font.SysFont(config.settings["font"],
                                                    int(self.font_size))
        self.medium_large_ui_font = pygame.font.SysFont(
            config.settings["font"], int(self.font_size * 1.5))
        self.larger_ui_font = pygame.font.SysFont(config.settings["font"],
                                                  int(self.font_size * 1.7))
        self.large_ui_font = pygame.font.SysFont(config.settings["font"],
                                                 int(self.font_size * 2))
        self.smaller_title_ui_font = pygame.font.SysFont(
            config.settings["title_font"], int(self.font_size * 3.5))
        self.title_ui_font = pygame.font.SysFont(config.settings["title_font"],
                                                 int(self.font_size * 5))
        self.standard_padding = Vector2D(self.font_size // 5,
                                         self.font_size // 5)
        self.wider_padding = Vector2D(self.font_size // 5 * 2,
                                      self.font_size // 5)
        self.larger_padding = Vector2D(self.font_size // 2,
                                       self.font_size // 2)
        self.very_wide_padding = Vector2D(self.font_size, self.font_size // 5)
        self.large_padding = Vector2D(self.font_size, self.font_size)
        self.extremely_wide_padding = Vector2D(self.font_size * 4,
                                               self.font_size // 2)
        self.standard_outline_size = Vector2D(self.font_size // 10,
                                              self.font_size // 10)
        self.cli_commands = {
            "help": self.CLIHelp,
            "tag add": self.CLIAddTag,
            "tag import": self.CLIImportTags,
            "tag export": self.CLIExportTags,
            "tag search": self.CLISearchTags,
            "tag view": self.CLIViewTag,
            "tag edit": self.CLIEditTag,
            "tag remove": self.CLIRemoveTag,
            "tag delete": self.CLIRemoveTag,
            "quit": self.CLIQuit,
            "font": self.CLIFontChange,
            "cls": self.CLIClear,
            "clear": self.CLIClear,
            "yes": self.CLIConfirm,
            "y": self.CLIConfirm,
            "no": self.CLIDeny,
            "n": self.CLIDeny,
            "stop": self.CLIDeny
        }
        self.file_dialog_used = False
        self.disallowed_characters = {
            "*": "asterisks",
            "&": "ampersands",
            "|": "vertical pipes",
            "!": "exclamations",
            "~": "tildes",
            "^": "carats",
            "(": "brackets",
            ")": "brackets",
            "+": "pluses"
        }
        self.disallowed_phrases = [
            "addweight", "calcweight", "and", "not", "or", "xor"
        ]

    def ConstructStartMenus(self, window):
        self.CreateLoadupMenu(window)
        debug.Log("Startup menu constructed successfully.")

    def ConstructMenus(self, window):
        self.ConstructFadeRectangle()
        self.CreateMainMenu(window)
        self.CreateTagsMenu(window)
        self.CreateTagAdditionMenu(window)
        self.CreateTagEditMenu(window)
        self.CreateErrorMenu(window)
        self.CreateNotificationMenu(window)
        self.CreateItemsMenu(window)
        self.CreateItemChangeMenu(window)
        self.CreateSearchesMenu(window)
        self.CreateSearchResultMenu(window)
        debug.Log("All menus constructed successfully.")

    def ChangeFade(self, new_fade):
        self.fade_rectangle.colour = (0, 0, 0, new_fade)
        self.fade_rectangle.UpdateImageColour()

    def ConstructFadeRectangle(self):
        self.fade_rectangle = Rectangle(config.settings["window_size"],
                                        (0, 0, 0, 0))

    def FinishStartup(self, window):
        encryption.CreateCiphers(config.settings["key"])
        SQL.LoadDatabase(config.settings["db_location"])
        self.ConstructMenus(window)
        self.loadup_component.AddCommands({"TYPE": "UPDATE BACKGROUND"}, {
            "TYPE":
            "TRANSITION",
            "TRANSITIONS":
            [{
                "ELEMENTS": self.loadup_component.tab_list[0],
                "STYLE": 25,
                "TIME": 1,
                "DELAY": 0,
                "TYPE": "LEAVING",
                "POST_ARGS": [{
                    "TYPE": "LEAVE",
                    "ID": ComponentID.LOADUP.value
                }]
            }, {
                "ELEMENTS": self.loadup_component.tab_list[1],
                "STYLE": 24,
                "TIME": 1,
                "DELAY": 0,
                "TYPE": "LEAVING"
            }, {
                "ELEMENTS": self.loadup_start_button,
                "STYLE": 1,
                "TIME": 1,
                "DELAY": 0.3,
                "TYPE": "LEAVING"
            }, {
                "ELEMENTS": ComponentID.MAIN.value,
                "STYLE": 1,
                "TIME": 1,
                "DELAY": 0.5,
                "TYPE": "JOINING"
            }]
        })

    def CreateLoadupMenu(self, window):
        self.loadup_component = StaticComponent(
            Vector2D(0, 0), config.settings["window_size"],
            config.settings["background_colour"])
        db_entry = Entry(self.larger_ui_font,
                         config.settings["window_width"] * 2 // 3,
                         padding=self.wider_padding,
                         outline_size=self.standard_outline_size,
                         empty_text="Enter location")
        db_entry.position = ScalePosition(Vector2D(0, 0),
                                          self.loadup_component.size,
                                          Vector2D(0.5, 0.3), db_entry.size)
        key_entry = Entry(self.larger_ui_font,
                          config.settings["window_width"] * 2 // 3,
                          padding=self.wider_padding,
                          outline_size=self.standard_outline_size,
                          empty_text="Enter key",
                          hide_text=True)
        key_entry.position = ScalePosition(Vector2D(0, 0),
                                           self.loadup_component.size,
                                           Vector2D(0.5, 0.5), key_entry.size)
        self.loadup_start_button = Button(
            "Start",
            self.large_ui_font,
            target=startup.GetKey,
            arguments=[self.loadup_component, self.FinishStartup, window],
            padding=self.wider_padding,
            outline_size=self.standard_outline_size,
            background_colour=(150, 150, 150))
        self.loadup_start_button.position = ScalePosition(
            Vector2D(0, 0), self.loadup_component.size, Vector2D(0.5, 0.7),
            self.loadup_start_button.size)
        self.loadup_component.AddUIElements(db_entry, key_entry,
                                            self.loadup_start_button)
        self.loadup_component.tab_list = [db_entry, key_entry]

        window.AddComponent(self.loadup_component, ComponentID.LOADUP.value,
                            True, True)

        debug.Log("Menu #1 loaded correctly.")

    def PrintToCLI(self, text):
        self.command_line_output.text += '\n' + text

    def CLIHelp(self, command):
        for line in [
                "\nHELP", "-------",
                "help - Provides help list for available commands",
                "tag add x - Adds a new tag to the database. See 'tag add help' for more",
                "tag import x - Imports & adds multiple tags. See 'tag import help' for more",
                "tag export x - Exports all existing tags. See 'tag export help' for more",
                "tag search x - Search for tags. See 'tag search help' for more",
                "tag view x - View a tag's information. See 'tag view help' for more",
                "tag edit x - Edit and update a tag's details. See 'tag edit help' for more",
                "tag remove x - Remove a tag. See 'tag remove help' for more",
                "font x - Changes the command line font to the font named x",
                "clear / cls - Clears the command line output",
                "quit - Quit the program",
                "More commands are currently under development."
        ]:
            self.PrintToCLI(line)

    def CLIAddTag(self, command):
        try:
            command = command.strip()
            tag_data = command.split(" ")[2:]
            RemoveStringFromList(tag_data, '')
            if tag_data[0].lower() == "help":
                self.PrintToCLI(
                    "\nEnter a tag in the following format:" +
                    '\n > tag add [name] "[description]" ([synonym1], [synonym2], ...) '
                    + "\nFor example, entering" +
                    '\n > tag add one "The number 1." (1, number_one, the_number_one)'
                    +
                    "\nwould add a tag with the name 'one', a description 'The number 1.', and"
                    + "\nthe synonyms '1', 'number_one' and 'the_number_one'.")
                return
            name = tag_data[0].lower()
            desc = SplitByCharacters(command, ["'", '"'])
            if len(desc) == 3:
                desc = desc[1]
            elif len(desc) == 2:
                self.PrintToCLI(
                    "That input was not understood. Maybe you forgot to close the"
                    + "\nquotation on your description?")
                return
            elif len(desc) == 1:
                desc = ''
            else:
                self.PrintToCLI(
                    "That input was not understood. Look at 'tag add help' for more"
                    + "\ninformation.")
                return
            synonym_text = SplitByCharacters(
                command, ["(", "[", "{", "<", ")", "]", "}", ">"])
            if len(synonym_text) == 3:
                synonym_text = synonym_text[1]
            elif len(synonym_text) == 2:
                self.PrintToCLI(
                    "That input was not understood. Maybe you forgot to close the"
                    + "\nparentheses around your synonyms?")
                return
            elif len(synonym_text) == 1:
                synonym_text = ''
            else:
                self.PrintToCLI(
                    "That input was not understood. Look at 'tag add help' for more"
                    + "\ninformation.")
                return
            split_text = synonym_text.split(",")
            synonyms = []
            for s in split_text:
                s = s.strip(" ")
                if len(s) > 0 and s not in synonyms:
                    synonyms.append(s)
            self.PrintToCLI(
                "Here is the information for the tag you entered:" +
                "\nNAME: {}".format(name) + "\nDESCRIPTION: {}".format(desc) +
                "\nSYNONYMS: {}".format(", ".join(synonyms)) +
                "\nDo you wish to add a tag with this information?")
            self.cli_history = [
                self.AttemptAddNewTag,
                [name, desc, synonyms, [self.main_menu_component, [2]], False],
                self.PrintToCLI, ["Tag addition process aborted."]
            ]
            debug.Log('Attempted to add a new tag through the CLI.')
        except:
            self.PrintToCLI(
                "That input was not understood. Look at 'tag add help' for more"
                + "\ninformation.")

    def CLIImportTags(self, command):
        command = command.strip()
        import_data = command.split(" ")[2:]
        if len(import_data) == 0:
            self.PrintToCLI(
                "That input was not understood. Look at 'tag import help' for"
                + "\nmore information.")
            return
        if import_data[0].lower() == "help":
            self.PrintToCLI(
                "\nImport tag data from a given file in the following format:"
                + '\n > tag import [path to file] ' +
                '\nImport tag data from a file you can manually select using:'
                + '\n > tag import file' +
                '\nImport tag data from your clipboard by typing either of:' +
                '\n > tag import clipboard' + '\n > tag import paste' +
                '\nOr import tag data directly by directly entering the data:'
                + '\n > tag import [data]')
        elif import_data[0].lower() in ["clipboard", "paste"]:
            self.ImportTagsFromClipboard()
            debug.Log(
                "Attempted to import tags from the clipboard through the CLI.")
        elif import_data[0].lower() in ["file", "choose"]:
            self.ImportTagsFromFile()
            debug.Log("Attempted to import tags from a file through the CLI.")
        elif command.endswith(".CVAL") or command.endswith(".txt"):
            file_path = "".join(import_data)
            self.ImportTagsFromFile(filename=file_path)
            debug.Log("Attempted to import tags from a file through the CLI.")
        else:
            self.AttemptTagImport("".join(import_data))
            debug.Log("Attempted to import tags directly from the CLI.")

    def CLIExportTags(self, command):
        command = command.strip()
        export_data = command.split(" ")[2:]
        if len(export_data) == 0:
            self.PrintToCLI(
                "That input was not understood. Look at 'tag export help' for"
                + "\nmore information.")
            return
        if export_data[0].lower() == "help":
            self.PrintToCLI(
                "\nExport tag data to a given file in the following format:" +
                '\n > tag export [path to file] ' +
                '\nExport tag data from a file you can manually select using:'
                + '\n > tag export file' +
                '\nExport tag data from your clipboard by typing either of:' +
                '\n > tag export clipboard' + '\n > tag export copy')
        elif export_data[0].lower() in ["clipboard", "copy"]:
            self.ExportTagsToClipboard()
            debug.Log(
                "Attempted to export tags to the clipboard through the CLI.")
        elif export_data[0].lower() in ["file", "choose"]:
            self.ExportTagsToFile()
            debug.Log("Attempted to export tags to a file through the CLI.")
        elif command.endswith(".CVAL") or command.endswith(".txt"):
            file_path = "".join(export_data)
            self.ExportTagsToFile(filename=file_path)
            debug.Log("Attempted to export tags to a file through the CLI.")
        else:
            self.PrintToCLI(
                "That input was not understood. Look at 'tag export help' for"
                + "\nmore information.")

    def CLISearchTags(self, command):
        command = command.strip()
        tag_data = command.split(" ")[2:]
        if len(tag_data) == 0:
            self.PrintToCLI(
                "That input was not understood. Look at 'tag search help' for"
                + "\nmore information.")
            return
        if tag_data[0].lower() == "help":
            self.PrintToCLI(
                "\nSearch for a tag in the following format:" +
                '\n > tag search [query] [distance] ' +
                '\nWhere the query is just the term you are searching with, and distance'
                +
                '\nis an integer from 0 to 100 (inclusive) indicating threshold similarity.'
                +
                '\n0 is no similarity and 100 is high similarity. You can also leave it blank:'
                + '\n > tag search [query]' +
                '\nA distance of around 60 is recommended.' +
                '\nCheck \'tag view help\' if you want to see more information about a tag.'
            )
            return
        query = tag_data[0].lower()
        if len(tag_data) > 1:
            try:
                distance = int(tag_data[1])
            except:
                self.PrintToCLI(
                    "That input was not understood. Make sure your entered" +
                    "\ndistance is an integer from 0-100. See 'tag search help' for more."
                )
                return
        else:
            distance = config.settings["levenshtein_search_threshold"]
        if len(query) == 0:
            self.PrintToCLI("No matches found.")
            return
        matches = GetTagMostSimilar(query, SQL.GetTagNames())
        tags = sorted(list(matches), key=lambda k: matches[k], reverse=True)
        for i, tag in enumerate(tags):
            if matches[tag] < distance:
                tags = tags[:i]
                break
        debug.Log(
            f'Searched for tags through the CLI. {len(tags)} matches found.')
        if len(tags) == 0:
            self.PrintToCLI("No matches found.")
            return
        to_print = f'{len(tags)} matches found:'
        for i, tag in enumerate(tags):
            to_print += f'\n{i+1}: {tag}'
        self.PrintToCLI(to_print)

    def CLIViewTag(self, command):
        command = command.strip()
        tag_data = command.split(" ")[2:]
        RemoveStringFromList(tag_data, '')
        if len(tag_data) == 0:
            self.PrintToCLI(
                "That input was not understood. Look at 'tag view help' for" +
                "\nmore information.")
            return
        if tag_data[0].lower() == "help":
            self.PrintToCLI(
                "\nView the information about a certain tag by using the following:"
                + '\n > tag view [tag name] ' + '\nYou can also use:' +
                '\n > tag view [synonym]' +
                '\nwhich will then attempt to find the tag based on its synonyms.'
                + '\nYou may also find the \'tag search\' command useful.')
            return
        name = "_".join(tag_data)
        data = SQL.GetTagData(name)
        debug.Log("Attempted to view a tag through the CLI.")
        if data == None:
            data = SQL.GetTagDataFromSynonym(name)
            if data == None:
                self.PrintToCLI(
                    "That tag/synonym could not be found. Look at 'tag view help'"
                    + "\nfor more information.")
                return
        self.PrintToCLI("\n NAME: {}".format(data["NAME"]) +
                        "\n DESCRIPTION: {}".format(data["DESCRIPTION"]) +
                        "\n SYNONYMS: {}".format(", ".join(data["SYNONYMS"])))

    def CLIEditTag(self, command):
        try:
            command = command.strip()
            tag_data = command.split(" ")[2:]
            RemoveStringFromList(tag_data, '')
            if len(tag_data) == 0:
                self.PrintToCLI(
                    "That input was not understood. Look at 'tag edit help' for"
                    + "\nmore information.")
                return
            if tag_data[0].lower() == "help":
                self.PrintToCLI(
                    "\nEdit the information about a certain tag by using the following:"
                    +
                    '\n > tag edit [name] [new name] "[description]" ([synonym1], [synonym2], ...) '
                    +
                    '\nIf you don\'t know a tag\'s name but know a synonym see \'tag view help\'.'
                    +
                    '\nUse * in any field (but name) to indicate that it should stay unchanged:'
                    + '\n > tag edit example * "Hello" *' +
                    '\nFor example will change the "example" tag\'s description to \'Hello\'.'
                    +
                    '\nYou can also put * as one of the synonyms to keep all current synonyms:'
                    + '\n> tag edit example2 * * (*, syn_1, syn_2)' +
                    '\nFor example keeps all old synonyms and adds \'syn_1\' and \'syn_2\'.'
                )
                return
            if len(tag_data) == 3 and tag_data[2].strip() == "*":
                self.PrintToCLI(
                    "Sorry, inputs in the form" +
                    "\n > tag edit [current name] [name] *" +
                    "\ncannot be understood. This is because it could be interpreted"
                    +
                    "\nas either the description or synonyms being left empty. Try"
                    + "\nusing either of the following formats instead:" +
                    "\n > tag edit [current name] [name] (*)      <no description>"
                    +
                    "\n > tag edit [current name] [name] * ()     <no synonyms>"
                )
                return
            name = tag_data[0].lower()
            current_data = SQL.GetTagData(name)
            if current_data == None:
                self.PrintToCLI(
                    "That tag could not be found. You might want to try the 'tag view' command."
                    + "\nSee 'tag edit help' for more information.")
                return
            new_name = tag_data[1].lower()
            if "*" in new_name:
                new_name = name
            if "*" in tag_data[2] and not CharactersInString(
                ["(", "[", "{", "<", ")", "]", "}", ">"],
                    tag_data[2]):  # if in desription
                desc = current_data["DESCRIPTION"]
            else:
                desc = SplitByCharacters(command, ["'", '"'])
                if len(desc) == 3:
                    desc = desc[1]
                elif len(desc) == 2:
                    self.PrintToCLI(
                        "That input was not understood. Maybe you forgot to close the"
                        + "\nquotation on your description?")
                    return
                elif len(desc) == 1:
                    desc = ''
                else:
                    self.PrintToCLI(
                        "That input was not understood. Look at 'tag edit help' for more"
                        + "\ninformation.")
                    return
            synonym_text = SplitByCharacters(
                command, ["(", "[", "{", "<", ")", "]", "}", ">"])
            if "*" in tag_data[-1] and len(synonym_text) == 1:
                # we have to check length to avoid catching cases like 'synonyms = (1, 2, 3, *)'
                synonyms = current_data["SYNONYMS"]
            else:
                if len(synonym_text) == 3:
                    synonym_text = synonym_text[1]
                elif len(synonym_text) == 2:
                    self.PrintToCLI(
                        "That input was not understood. Maybe you forgot to close the"
                        + "\nparentheses around your synonyms?")
                    return
                elif len(synonym_text) == 1:
                    synonym_text = ''
                else:
                    self.PrintToCLI(
                        "That input was not understood. Look at 'tag edit help' for more"
                        + "\ninformation.")
                    return
                split_text = synonym_text.split(",")
                synonyms = []
                for s in split_text:
                    s = s.strip(" ")
                    if len(s) > 0 and s not in synonyms:
                        if s == "*":
                            for synonym in current_data["SYNONYMS"]:
                                if synonym not in synonyms:
                                    synonyms.append(synonym)
                        else:
                            synonyms.append(s)
            debug.Log("Attempted to edit a tag through the CLI.")
            self.PrintToCLI(
                "Here is the current information for the tag:" +
                "\n NAME: {}".format(name) +
                "\n DESCRIPTION: {}".format(current_data["DESCRIPTION"]) +
                "\n SYNONYMS: {}".format(", ".join(current_data["SYNONYMS"])) +
                "\nHere is the edited information for the tag:" +
                "\n NAME: {}".format(new_name) +
                "\n DESCRIPTION: {}".format(desc) +
                "\n SYNONYMS: {}".format(", ".join(synonyms)) +
                "\nDo you wish to update the tag with this information?")
            self.cli_history = [
                self.AttemptUpdateTag,
                [
                    name, current_data["SYNONYMS"], new_name, desc, synonyms,
                    [self.main_menu_component, [2]], False
                ], self.PrintToCLI, ["Tag editing process aborted."]
            ]
        except:
            self.PrintToCLI(
                "That input was not understood. Look at 'tag edit help' for more"
                + "\ninformation.")

    def CLIRemoveTag(self, command):
        command = command.strip()
        tag_data = command.split(" ")[2:]
        if len(tag_data) == 0:
            self.PrintToCLI(
                "That input was not understood. Look at 'tag remove help' for"
                + "\nmore information.")
            return
        if tag_data[0].lower() == "help":
            self.PrintToCLI(
                "\nRemove a tag by issuing a command in the following format:"
                + '\n > tag remove [name]' +
                '\nIf you don\'t know a tag\'s name but know a synonym see \'tag view help\'.'
                +
                '\nIf you are trying to find a specific tag, see \'tag search help\'.'
            )
            return
        name = tag_data[0].lower()
        tags = SQL.GetTagNames()
        if name in tags:
            SQL.RemoveTag(name)
            self.AddNotification("Tag deleted successfully")
            debug.Log("Removed a tag through the CLI.")
        else:
            self.AddNotification("Tag deletion failed")
            debug.Log("Failed to remove a tag through the CLI.")
            self.PrintToCLI(
                "That tag could not be found. Look at 'tag remove help' for" +
                "\nmore information")

    def CLIConfirm(self, command):
        if len(self.cli_history) > 0:
            debug.Log(
                "Decided to continue with their previous descision in the CLI."
            )
            self.cli_history[0](*self.cli_history[1])
        else:
            self.PrintToCLI(
                "Unknown Command. Type 'help' to show a list of available commands."
            )

    def CLIDeny(self, command):
        if len(self.cli_history) > 0:
            debug.Log(
                "(CLI) Decided to abort their previous decision in the CLI.")
            self.cli_history[2](*self.cli_history[3])
        else:
            self.PrintToCLI(
                "Unknown Command. Type 'help' to show a list of available commands."
            )

    def CLIQuit(self, command):
        if command.lower() == "quit help":
            self.PrintToCLI(
                "Typing 'quit' into the interface will quit the program.")
        else:
            debug.Log("Typed 'quit' into the CLI.")
            self.main_menu_component.AddCommand({"TYPE": "STOP"})

    def CLIFontChange(self, command):
        try:
            font_name = "".join(command.lower().strip().split(" ")[1:])
            if font_name == 'default':
                font_name = config.settings["font"]
            elif font_name == 'help':
                self.PrintToCLI(
                    "Typing 'font x' (where x is the name of a font, e.g. 'font comicsansms') will\nchange the command line interface's font to the specified font."
                )
                return
            if font_name not in pygame.font.get_fonts():
                self.PrintToCLI(
                    "That font could not be found. Type 'font help' for more.")
                return
            new_font = pygame.font.SysFont(font_name, int(self.font_size))
            self.command_line_entry.font = new_font
            self.command_line_entry.UpdateText()
            self.command_line_entry.UpdateImage()
            self.command_line_output.font = new_font
            self.command_line_output.UpdateImage()
            self.PrintToCLI("Font applied.")
            debug.Log(f'Applied new font {font_name} through the CLI.')
        except:
            self.PrintToCLI(
                "That font could not be applied. Type 'font help' for more.")

    def CLIClear(self, command):
        self.command_line_output.text = ''
        self.command_line_output.current_scroll = 0
        self.command_line_output.UpdateImage()
        debug.Log("Cleared the CLI.")

    def UpdateCommandLineOutput(self, data):
        if len(data) > 100:
            display_data = data[:100] + "..."
        else:
            display_data = data
        if len(self.command_line_output.text) == 0:
            self.command_line_output.text += f' > {display_data}'
        else:
            self.PrintToCLI(f"\n > {display_data}")
        input_command = data.lower().strip()
        for command in self.cli_commands:
            if input_command.startswith(command):
                self.cli_commands[command](data)
                return
        # only run if no other commands matched
        self.PrintToCLI(
            "Unknown Command. Type 'help' to show a list of available commands."
        )

    def CreateMainMenu(self, window):  # 2
        self.main_menu_component = StaticComponent(
            Vector2D(0, 0), config.settings["window_size"], (0, 0, 0, 0))
        title_size = Vector2D(int(config.settings["window_width"] // 5 * 3.5),
                              config.settings["window_width"] // 5)
        title_image = pygame.transform.scale(
            pygame.image.load('gui\\images\\Title.png'), tuple(title_size))
        title = ImageElement(title_image)
        title.position = ScalePosition(Vector2D(0, 0),
                                       self.main_menu_component.size,
                                       Vector2D(0.5, 0.15), title_size)
        version_label = Label(config.version,
                              self.standard_ui_font,
                              text_colour=(150, 150, 150))
        version_label.position = ScalePosition(Vector2D(0, 0),
                                               self.main_menu_component.size,
                                               Vector2D(0,
                                                        0), version_label.size,
                                               Vector2D(0, 0))
        version_label.position.x += self.standard_padding.x
        button_container = RegulatedContainer(
            1, 4, Vector2D(0, 0),
            Vector2D(0, self.main_menu_component.height // 30))
        button_size = Vector2D(self.main_menu_component.width // 4,
                               self.main_menu_component.height // 10)
        outline_size = Vector2D(self.main_menu_component.width // 400,
                                self.main_menu_component.width // 400)
        self.main_tags_button = Button(
            "Tags",
            self.large_ui_font,
            target=self.main_menu_component.AddCommands,
            arguments=[{
                "TYPE": "JOIN",
                "ID": ComponentID.TAG_LIST.value,
            }, {
                "TYPE":
                "MOVE",
                "ID":
                ComponentID.TAG_LIST.value,
                "POSITION":
                Vector2D(0, config.settings["window_height"] // 7)
            }, {
                "TYPE": "DEACTIVATE",
                "ID": ComponentID.TAG_LIST.value,
                "CACHE": False
            }, {
                "TYPE":
                "TRANSITION",
                "TRANSITIONS": [{
                    "ELEMENTS": ComponentID.MAIN.value,
                    "STYLE": 1,
                    "TIME": 1,
                    "DELAY": 0,
                    "TYPE": "LEAVING"
                }, {
                    "ELEMENTS": ComponentID.TAG_FIRST_BAR.value,
                    "STYLE": 7,
                    "TIME": 0.5,
                    "DELAY": 0.9,
                    "TYPE": "JOINING"
                }]
            }],
            padding=MakeElementEqualSize("Tags", self.large_ui_font,
                                         button_size),
            outline_size=outline_size,
            pressed_background_colour=(200, 200, 200))
        items_button = Button("Items",
                              self.large_ui_font,
                              target=self.main_menu_component.AddCommands,
                              arguments=[{
                                  "TYPE":
                                  "TRANSITION",
                                  "TRANSITIONS": [{
                                      "ELEMENTS":
                                      ComponentID.MAIN.value,
                                      "STYLE":
                                      2,
                                      "TIME":
                                      1,
                                      "DELAY":
                                      0,
                                      "TYPE":
                                      "LEAVING"
                                  }, {
                                      "ELEMENTS":
                                      ComponentID.ITEM_FIRST_BAR.value,
                                      "STYLE":
                                      2,
                                      "TIME":
                                      1,
                                      "DELAY":
                                      0,
                                      "TYPE":
                                      "JOINING"
                                  }]
                              }],
                              padding=MakeElementEqualSize(
                                  "Items", self.large_ui_font, button_size),
                              outline_size=outline_size,
                              pressed_background_colour=(200, 200, 200))
        search_button = Button("Search",
                               self.large_ui_font,
                               target=self.main_menu_component.AddCommands,
                               arguments=[{
                                   "TYPE":
                                   "TRANSITION",
                                   "TRANSITIONS": [{
                                       "ELEMENTS":
                                       ComponentID.MAIN.value,
                                       "STYLE":
                                       25,
                                       "TIME":
                                       1,
                                       "DELAY":
                                       0,
                                       "TYPE":
                                       "LEAVING"
                                   }, {
                                       "ELEMENTS":
                                       ComponentID.SEARCH.value,
                                       "STYLE":
                                       25,
                                       "TIME":
                                       1,
                                       "DELAY":
                                       0,
                                       "TYPE":
                                       "JOINING"
                                   }]
                               }],
                               padding=MakeElementEqualSize(
                                   "Search", self.large_ui_font, button_size),
                               outline_size=outline_size,
                               pressed_background_colour=(200, 200, 200))
        exit_button = Button("Exit",
                             self.large_ui_font,
                             target=self.main_menu_component.AddCommand,
                             arguments={"TYPE": "STOP"},
                             padding=MakeElementEqualSize(
                                 "Exit", self.large_ui_font, button_size),
                             outline_size=outline_size,
                             background_colour=(237, 27, 36),
                             pressed_background_colour=(237, 27, 36),
                             text_colour=(255, 255, 255))
        buttons = [
            self.main_tags_button, items_button, search_button, exit_button
        ]
        button_container.AddElements(*buttons)
        button_container.position = ScalePosition(
            Vector2D(0, 0), self.main_menu_component.size,
            Vector2D(1 / 4, 0.6), button_container.size)

        command_line_container = Container(
            1, 2, Vector2D(0, 0), Vector2D(0, -self.standard_outline_size.y))
        self.command_line_entry = FunctionalEntry(
            self.standard_ui_font,
            self.main_menu_component.width // 2,
            self.UpdateCommandLineOutput,
            padding=self.standard_padding,
            outline_size=self.standard_outline_size,
            empty_text="Type 'help' for help!",
            text_colour=(255, 255, 255),
            background_colour=(50, 50, 50))
        self.command_line_output = AdvancedLabel(
            '',
            self.standard_ui_font,
            Vector2D(self.main_menu_component.width // 2,
                     self.main_menu_component.height // 3 * 2),
            padding=self.standard_padding,
            outline_size=self.standard_outline_size,
            background_colour=(50, 50, 50),
            outline_colour=(0, 0, 0),
            text_colour=(255, 255, 255),
            line_seperation=self.main_menu_component.height // 400,
            auto_scroll_position=1)
        self.cli_history = []
        command_line_container.AddElements(self.command_line_output,
                                           self.command_line_entry)
        command_line_container.position = ScalePosition(
            Vector2D(0, 0), self.main_menu_component.size, Vector2D(1, 1),
            command_line_container.size, Vector2D(1, 1))

        self.main_menu_component.AddUIElements(title, version_label,
                                               button_container,
                                               command_line_container)
        window.AddComponent(self.main_menu_component, ComponentID.MAIN.value,
                            False, False)

    def SetupDefaultFileDialog(self):
        from tkinter import Tk, PhotoImage
        root = Tk()
        root.withdraw()  # instantly withdraw so the tk window doesn't pop up
        root.tk.call('wm', 'iconphoto', root._w,
                     PhotoImage(file='gui\\images\\Logo32.png'))

    def AttemptTagImport(self, ImportText):
        from base64 import b64encode as EncodeB64
        from json import loads as LoadJSON
        try:
            imported_text = encryption.DecryptTextWithKey(
                EncodeB64(config.settings["key"]), ImportText)
            tag_data = LoadJSON(imported_text)
            successful = 0
            failed = []
            for tag in tag_data:
                success = self.AttemptAddNewTag(tag[0], tag[1], tag[2], [
                    self.tag_first_bar,
                    [ComponentID.TAG_SECOND_BAR, ComponentID.TAG_LIST]
                ], False, False)
                if success:
                    successful += 1
                else:
                    failed.append(tag[0])
            self.AddNotification(
                "{} tags successfully added & {} failed".format(
                    successful, len(failed)),
                display_time=8)
            debug.Log(
                f'Successfully imported {successful} tags and failed to import {len(failed)} tags.'
            )
            if successful > 0:
                self.RefreshTags()
        except:
            self.AddNotification("Failed to import tags")
            debug.Log("Failed to import tags.")

    def ImportTagsFromClipboard(self):
        from pyperclip import paste as PasteFromClipboard
        self.AttemptTagImport(PasteFromClipboard().strip())

    def ImportTagsFromFile(self, filename=None):
        try:
            if filename == None:
                if not self.file_dialog_used:
                    self.SetupDefaultFileDialog()
                    self.file_dialog_used = True
                from tkinter.filedialog import askopenfilename as AskOpenFileName
                filename = AskOpenFileName(
                    title="Select a file to import tag data from",
                    filetypes=(("CVAL files", "*.CVAL"), ("Text files",
                                                          "*.txt")))
            if filename != '':
                debug.Log(f'Attempted to import tags from a file.')
                with open(filename, "r") as f:
                    data = f.read()
                    f.close()
                self.AttemptTagImport(data.strip())
        except FileNotFoundError:
            self.AddNotification("The specified file could not be found")
        except:
            self.AddNotification("An error occurred accessing the file")

    def GetTagExport(self):
        from base64 import b64encode as EncodeB64
        from json import dumps as DumpJSON
        tag_data = DumpJSON(SQL.GetAllTagData())
        return encryption.EncryptTextWithKey(EncodeB64(config.settings["key"]),
                                             tag_data)

    def ExportTagsToClipboard(self):
        from pyperclip import copy as CopyToClipboard
        CopyToClipboard(self.GetTagExport())
        self.AddNotification("Tag data copied to clipboard")

    def ExportTagsToFile(self, filename=None):
        try:
            if filename == None:
                if not self.file_dialog_used:
                    self.SetupDefaultFileDialog()
                    self.file_dialog_used = True
                from tkinter.filedialog import asksaveasfile as AskSaveAsFile
                file_ = AskSaveAsFile(
                    title="Create a file to save tag data to",
                    filetypes=(("CVAL files", "*.CVAL"), ("Text files",
                                                          "*.txt")),
                    defaultextension="CVAL")
            else:
                file_ = open(filename, 'w+')
            if file_ != None:
                debug.Log(f'Exported tag information to a file.')
                file_.write(self.GetTagExport())
                file_.close()
                self.AddNotification("Tag data successfully exported to file")
        except:
            self.AddNotification("An error occurred accessing the file")

    def UpdateDisplayedTags(self):
        columns = self.tags_container.columns
        start_index = self.tags_container.current_row * columns
        max_index = len(self.tags) - 1
        updated_max_row = False
        for i, button in enumerate(self.tags_buttons):
            if (start_index + i) > max_index:
                if not updated_max_row:
                    self.tags_container.max_row = self.tags_container.current_row
                    updated_max_row = True
                button.active = False
                button.hidden = True
            else:
                tag_info = self.tags[start_index + i]
                button.arguments = tag_info[0]
                button.text = tag_info[1]
                button.padding = tag_info[2]
                button.tooltip_image = tag_info[3]
                button.UpdateImage()
                button.active = tag_info[4]
                button.hidden = not tag_info[4]
            if button.arguments in self.selected_tags:
                button.pressed = True
            else:
                button.pressed = False
        if not updated_max_row and (start_index + i + 1) > max_index:
            self.tags_container.max_row = self.tags_container.current_row

    def ReplaceLoadedTag(self, replace_name, new_name):
        debug.Log("Replaced loaded tag.")
        replace_name = replace_name.lower().strip()
        new_name = new_name.lower().strip()
        if replace_name not in [tag[0] for tag in self.tags]:
            return
        text = self.GetDisplayText(new_name, self.standard_ui_font,
                                   self.tag_text_width)
        tooltip = Label(new_name,
                        self.standard_ui_font,
                        padding=self.standard_padding,
                        outline_size=self.standard_outline_size,
                        background_colour=(150, 150, 150),
                        outline_colour=(0, 0, 0)).image
        target_width = self.tag_text_width + 2 * self.wider_padding.x
        button_padding = Vector2D(
            MakeElementEqualSize(text, self.standard_ui_font,
                                 Vector2D(target_width, 0)).x,
            self.wider_padding.y)
        for tag in self.tags:
            if tag[0] == replace_name:
                tag[0] = new_name
                tag[1] = text
                tag[2] = button_padding
                tag[3] = tooltip
                break
        for tag in self.original_tags:
            if tag[0] == replace_name:
                tag[0] = new_name
                tag[1] = text
                tag[2] = button_padding
                tag[3] = tooltip
                break
        if len(self.tags_menu_search_entry.text) > 0:
            self.UpdateSearchedTags(self.tags_menu_search_entry.text)
        else:
            self.UpdateDisplayedTags()

    def LoadTag(self, tag_name, do_update_tags=True):
        tag_name = tag_name.lower().strip()
        if tag_name in self.tags:
            return
        text = self.GetDisplayText(tag_name, self.standard_ui_font,
                                   self.tag_text_width)
        tooltip = Label(tag_name,
                        self.standard_ui_font,
                        padding=self.standard_padding,
                        outline_size=self.standard_outline_size,
                        background_colour=(150, 150, 150),
                        outline_colour=(0, 0, 0)).image
        target_width = self.tag_text_width + 2 * self.wider_padding.x
        button_padding = Vector2D(
            MakeElementEqualSize(text, self.standard_ui_font,
                                 Vector2D(target_width, 0)).x,
            self.wider_padding.y)
        self.tags.append([tag_name, text, button_padding, tooltip, True])
        if (len(self.tags) % self.tags_container.columns
                == 1) or (self.tags_container.columns == 1):
            self.tags_container.max_row += 1
        if do_update_tags:
            self.original_tags.append(self.tags[-1])
            if len(self.tags_menu_search_entry.text) > 0:
                self.UpdateSearchedTags(self.tags_menu_search_entry.text)
            else:
                self.UpdateDisplayedTags()

    def UnloadTag(self, tag_name, do_update_tags=True):
        if tag_name in [i[0] for i in self.tags]:
            for tag in self.tags:
                if tag[0] == tag_name:
                    self.tags.remove(tag)
                    if do_update_tags:
                        self.original_tags.remove(tag)
                    break
        else:
            return
        if len(self.tags) % self.tags_container.columns == 0:
            self.tags_container.max_row -= 1
            self.tags_container.current_row -= 1
            if self.tags_container.current_row <= 0:
                self.tags_container.current_row = 0
        if do_update_tags:  # optional so not inefficient when adding mass tags
            if len(self.tags_menu_search_entry.text) > 0:
                self.UpdateSearchedTags(self.tags_menu_search_entry.text)
            else:
                self.UpdateDisplayedTags()

    def RefreshTags(self):
        tags = SQL.GetTagNames()
        tag_names = [i[0] for i in self.tags]
        for tag in tags:
            if (tag not in tag_names) and (tag not in self.excluded_tag_data):
                self.LoadTag(tag, do_update_tags=False)
        for tag in tag_names:
            if tag not in tags:
                self.UnloadTag(tag, do_update_tags=False)
        self.tags_container.current_row = 0
        self.UpdateDisplayedTags()
        self.original_tags = [t for t in self.tags]

    def ViewTag(self, tag_name):
        tag_data = SQL.GetTagData(tag_name)
        self.selected_tag_data = tag_data.copy()
        if self.on_bar == 4:
            debug.Log("Selected a tag to add the new tag to as a synonym.")
            new_synonyms = tag_data["SYNONYMS"].copy()
            new_synonyms.append(self.temp_tags[1][0])
            updated = self.AttemptUpdateTag(old_name=tag_name,
                                            old_synonyms=tag_data["SYNONYMS"],
                                            name=tag_name,
                                            desc=tag_data["DESCRIPTION"],
                                            synonyms=new_synonyms,
                                            error_args=None,
                                            do_transitions=False,
                                            do_notifications=True)
            self.in_tag_menu = True
            self.AddUnknownAsSynonym(self.temp_tags[1],
                                     tag_name=tag_name,
                                     updated=updated,
                                     called=2)
            return
        debug.Log("Viewed a specific tag through the tag menu.")
        self.selected_tags = []
        self.UpdateDisplayedTags()
        self.ResetTagAdditionMenu()
        self.tag_name_entry.text = tag_data["NAME"]
        self.tag_name_entry.UpdateText()
        self.tag_desc_entry.text = tag_data["DESCRIPTION"]
        self.tag_desc_entry.UpdateText()
        for s in tag_data["SYNONYMS"]:
            self.AddSynonym(s, update_suggested=False)
        self.UpdateSuggestedSynonyms(exclude=[tag_data["NAME"]])
        self.synonym_suggestion_component.updated_upon_exit = False
        self.synonym_suggestion_component.Update()
        self.is_adding_tag = False
        self.tags_list_component.AddCommands(
            {
                "TYPE": "JOIN",
                "ID": [ComponentID.TAG_FADE_LAYER.value]
            }, {
                "TYPE": "EXECUTE",
                "FUNCTION": self.ChangeFade,
                "ARGUMENTS": [0],
                "KWARGUMENTS": {}
            }, {
                "TYPE":
                "DEACTIVATE",
                "ID": [
                    ComponentID.TAG_FIRST_BAR.value,
                    ComponentID.TAG_SECOND_BAR.value,
                    ComponentID.TAG_LIST.value
                ],
                "CACHE":
                True
            }, {
                "TYPE":
                "TRANSITION",
                "TRANSITIONS": [{
                    "ELEMENTS": (self.ChangeFade, 0),
                    "STYLE":
                    5,
                    "TIME":
                    0.5,
                    "DELAY":
                    0,
                    "TYPE":
                    "JOINING",
                    "POST_ARGS": [{
                        "TYPE": "DEACTIVATE",
                        "ID": ComponentID.TAG_FADE_LAYER.value,
                        "CACHE": True
                    }]
                }, {
                    "ELEMENTS": ComponentID.TAG_EDIT.value,
                    "STYLE": 6,
                    "TIME": 0.5,
                    "DELAY": 0,
                    "TYPE": "JOINING"
                }, {
                    "ELEMENTS": ComponentID.TAG_CHANGE_EXIT.value,
                    "STYLE": 11,
                    "TIME": 1.25,
                    "DELAY": 0.5,
                    "TYPE": "JOINING"
                }, {
                    "ELEMENTS": ComponentID.TAG_ADD_SUGGESTIONS.value,
                    "STYLE": 12,
                    "TIME": 0.5,
                    "DELAY": 0,
                    "TYPE": "JOINING"
                }, {
                    "ELEMENTS": ComponentID.TAG_ADD_SYNONYMS.value,
                    "STYLE": 13,
                    "TIME": 0.5,
                    "DELAY": 0,
                    "TYPE": "JOINING"
                }]
            })

    def SelectTag(self, pressed, tag_name):
        if not self.tags_menu_remove_button.pressed:
            self.ViewTag(tag_name)
            return
        if pressed:
            self.selected_tags.append(tag_name)
        else:
            self.selected_tags.remove(tag_name)
        self.UpdateDisplayedTags()

    def RemoveSelectedTags(self, pressed):
        if not pressed:
            SQL.RemoveTags(self.selected_tags)
            for tag in self.selected_tags:
                self.UnloadTag(tag, do_update_tags=False)
            to_remove = []
            for tag in self.original_tags:
                if tag[0] in self.selected_tags:
                    to_remove.append(tag)
            for tag in to_remove:
                self.original_tags.remove(tag)
            if len(self.selected_tags) > 0:
                self.AddNotification("Tags successfully removed")
                debug.Log(
                    f'Successfully removed {len(self.selected_tags)} tags')
            self.selected_tags = []
            self.UpdateDisplayedTags()

    def LoadSecondTagsBar(self, *arguments):
        debug.Log("Opened the extra options bar in the tag menu.")
        self.tag_first_bar.AddCommands(*arguments)
        self.on_bar = 2

    def UnloadSecondTagsBar(self, *arguments):
        debug.Log("Closed the extra options bar in the tag menu.")
        self.tag_second_bar.AddCommands(*arguments)
        self.on_bar = 1

    def LoadThirdTagsBar(self, *arguments):
        debug.Log("Opened the tag selection menu for adding tags to items.")
        self.item_add_component.AddCommands(*arguments)
        self.on_bar = 3

    def UnloadThirdTagsBar(self, *arguments):
        debug.Log("Quit the tag selection menu for adding tags to items.")
        button_tags = [button.arguments for button in self.item_tags_buttons]
        for tag in self.selected_tags:
            if tag not in button_tags:
                self.AddItemTag(tag)
        for tag in button_tags:
            if tag not in self.selected_tags:
                self.RemoveItemTag(tag)
        self.tag_third_bar.AddCommands(*arguments)
        self.on_bar = 1

    def LoadFourthTagsBar(self, *arguments):
        debug.Log(
            "Opened the tag selection menu to add a new tag as a synonym of an existing tag."
        )
        self.error_component.AddCommands(*arguments)
        self.on_bar = 4
        self.in_tag_menu = False

    def UnloadFourthTagsBar(self, *arguments):
        debug.Log(
            "Quit the tag selection menu for adding a new tag as a synonym of an existing tag."
        )
        self.in_tag_menu = True
        self.selected_tags = self.temp_tags[0]
        self.tag_fourth_bar.AddCommands(*arguments)
        self.on_bar = 1

    def UpdateTagsFromResults(self, matches):
        for tag in self.tags:
            tag_name = tag[0]
            if tag_name not in matches.keys():
                tag[4] = False
                matches[tag_name] = 0
            elif matches[tag_name] < config.settings[
                    "levenshtein_search_threshold"]:
                tag[4] = False
            else:
                tag[4] = True
        self.tags = sorted(self.tags,
                           key=lambda k: matches[k[0]],
                           reverse=True)
        self.UpdateDisplayedTags()

    def UpdateSearchedTags(self, new_text):
        self.tags_container.current_row = 0
        if len(new_text) == 0:
            self.tags = [t[:4] + [True] for t in self.original_tags]
            self.UpdateDisplayedTags()
            return
        matches = GetTagMostSimilar(new_text.lower(),
                                    [tag[0] for tag in self.tags])
        self.tags_list_component.AddCommand({
            "TYPE": "EXECUTE",
            "FUNCTION": self.UpdateTagsFromResults,
            "ARGUMENTS": [matches],
            "KWARGUMENTS": {},
            "THREADED": True
        })

    def ResetTagsMenuFromThirdBar(self):
        self.excluded_tag_data = self.category_list.copy()
        self.ResetTagsMenu(selection_mode=True, reset_tag_bar=False)

    def ResetTagsMenuFromFourthBar(self):
        self.excluded_tag_data = []
        self.ResetTagsMenu(selection_mode=False, reset_tag_bar=False)

    def LoadTagAdditionMenu(self, *arguments):
        if self.on_bar == 1:
            self.tag_first_bar.AddCommands(*arguments)
        else:
            self.tag_third_bar.AddCommands(*arguments)

    def ResetTagsMenu(self, selection_mode=False, reset_tag_bar=True):
        debug.Log("Reset the tags menu.")
        if not selection_mode:
            self.selected_tags = []
        if reset_tag_bar:
            self.on_bar = 1
            self.excluded_tag_data = []
            self.in_tag_menu = False
        self.tags = []
        self.RefreshTags()
        self.tags_menu_remove_button.pressed = selection_mode
        self.tags_menu_search_entry.Reset()
        for button in self.tags_buttons:
            button.position = Vector2D(-config.settings["window_width"], 0)

    def CreateTagsMenu(self, window):
        self.tag_first_bar = StaticComponent(
            Vector2D(0, 0),
            Vector2D(config.settings["window_width"],
                     config.settings["window_height"] // 7), (50, 50, 50))
        back_button = Button("Back",
                             self.larger_ui_font,
                             target=self.tag_first_bar.AddCommands,
                             arguments={
                                 "TYPE":
                                 "TRANSITION",
                                 "TRANSITIONS": [{
                                     "ELEMENTS": [
                                         ComponentID.TAG_FIRST_BAR.value,
                                         ComponentID.TAG_LIST.value
                                     ],
                                     "STYLE":
                                     2,
                                     "TIME":
                                     1,
                                     "DELAY":
                                     0,
                                     "TYPE":
                                     "LEAVING"
                                 }, {
                                     "ELEMENTS": ComponentID.MAIN.value,
                                     "STYLE": 2,
                                     "TIME": 1,
                                     "DELAY": 0,
                                     "TYPE": "JOINING"
                                 }]
                             },
                             padding=self.wider_padding,
                             outline_size=self.standard_outline_size,
                             outline_colour=(255, 255, 255),
                             pressed_background_colour=(200, 200, 200))
        self.tags_menu_remove_button = CheckButton(
            "Remove tags",
            self.larger_ui_font,
            self.RemoveSelectedTags,
            padding=self.wider_padding,
            outline_size=self.standard_outline_size,
            background_colour=(192, 57, 43),
            pressed_background_colour=(142, 7, 0),
            outline_colour=(242, 107, 93),
            text_colour=(255, 255, 255))
        self.tags_menu_remove_button.pressed_image = CheckButton(
            "Delete",
            self.larger_ui_font,
            None,
            padding=MakeElementEqualSize(
                "Delete", self.larger_ui_font,
                self.tags_menu_remove_button.size -
                self.standard_outline_size * 2),
            outline_size=self.standard_outline_size,
            background_colour=(142, 7, 0),
            outline_colour=(242, 107, 93),
            text_colour=(255, 255, 255)).unpressed_image.copy()
        self.tags_menu_remove_button.pressed_image.convert_alpha()
        self.tags_menu_search_entry = ConstantFunctionalEntry(
            self.larger_ui_font,
            config.settings["window_width"] // 2,
            self.UpdateSearchedTags,
            send_text=True,
            padding=self.wider_padding,
            outline_size=self.standard_outline_size,
            empty_text="Search for tags",
            outline_colour=(255, 255, 255),
            empty_text_colour=(170, 170, 170))
        add_new_button = Button(
            "Add new",
            self.larger_ui_font,
            target=self.LoadTagAdditionMenu,
            arguments=[{
                "TYPE": "JOIN",
                "ID": ComponentID.TAG_FADE_LAYER.value
            }, {
                "TYPE":
                "TRANSITION",
                "TRANSITIONS": [{
                    "ELEMENTS": (self.ChangeFade, 0),
                    "STYLE":
                    5,
                    "TIME":
                    0.5,
                    "DELAY":
                    0,
                    "TYPE":
                    "JOINING",
                    "POST_ARGS": [{
                        "TYPE": "DEACTIVATE",
                        "ID": ComponentID.TAG_FADE_LAYER.value,
                        "CACHE": True
                    }]
                }, {
                    "ELEMENTS": ComponentID.TAG_ADD.value,
                    "STYLE": 6,
                    "TIME": 0.5,
                    "DELAY": 0,
                    "TYPE": "JOINING"
                }, {
                    "ELEMENTS": ComponentID.TAG_CHANGE_EXIT.value,
                    "STYLE": 11,
                    "TIME": 1.25,
                    "DELAY": 0.5,
                    "TYPE": "JOINING"
                }, {
                    "ELEMENTS": ComponentID.TAG_ADD_SUGGESTIONS.value,
                    "STYLE": 12,
                    "TIME": 0.5,
                    "DELAY": 0,
                    "TYPE": "JOINING"
                }, {
                    "ELEMENTS": ComponentID.TAG_ADD_SYNONYMS.value,
                    "STYLE": 13,
                    "TIME": 0.5,
                    "DELAY": 0,
                    "TYPE": "JOINING"
                }]
            }, {
                "TYPE": "EXECUTE",
                "FUNCTION": self.ChangeFade,
                "ARGUMENTS": [0],
                "KWARGUMENTS": {}
            }, {
                "TYPE":
                "DEACTIVATE",
                "ID":  # second bar and third bar value not necessary but used for consistency with the tag edit menu to save loading time and memory  TODO update in called function
                [ComponentID.TAG_FIRST_BAR.value, ComponentID.TAG_SECOND_BAR.value, ComponentID.TAG_THIRD_BAR.value, ComponentID.TAG_LIST.value],
                "CACHE":
                True
            }],
            padding=self.wider_padding,
            outline_size=self.standard_outline_size,
            background_colour=(37, 123, 200),
            pressed_background_colour=(37, 123, 200),
            outline_colour=(255, 255, 255),
            text_colour=(255, 255, 255))
        other_options_button = Button(" + ",
                                      self.larger_ui_font,
                                      self.LoadSecondTagsBar,
                                      arguments=[{
                                          "TYPE":
                                          "DEACTIVATE",
                                          "ID":
                                          ComponentID.TAG_FIRST_BAR.value,
                                          "CACHE":
                                          True
                                      }, {
                                          "TYPE":
                                          "TRANSITION",
                                          "TRANSITIONS": [{
                                              "ELEMENTS":
                                              ComponentID.TAG_SECOND_BAR.value,
                                              "STYLE":
                                              19,
                                              "TIME":
                                              1,
                                              "DELAY":
                                              0,
                                              "TYPE":
                                              "JOINING"
                                          }]
                                      }],
                                      padding=self.wider_padding,
                                      outline_size=self.standard_outline_size,
                                      background_colour=(37, 123, 200),
                                      pressed_background_colour=(37, 123, 200),
                                      outline_colour=(255, 255, 255),
                                      text_colour=(255, 255, 255))
        top_bar_container = Container(5, 1, inner_padding=self.wider_padding)
        top_bar_container.AddElements(back_button,
                                      self.tags_menu_remove_button,
                                      self.tags_menu_search_entry,
                                      add_new_button, other_options_button)
        top_bar_container.position = ScalePosition(Vector2D(0, 0),
                                                   self.tag_first_bar.size,
                                                   Vector2D(0.5, 0.5),
                                                   top_bar_container.size,
                                                   Vector2D(0.5, 0.5))
        self.tag_first_bar.AddUIElements(top_bar_container)
        self.tag_first_bar.reset_func = self.ResetTagsMenu

        self.tag_second_bar = StaticComponent(
            Vector2D(0, 0),
            Vector2D(config.settings["window_width"],
                     config.settings["window_height"] // 7), (50, 50, 50))
        self.on_bar = 1
        import_button = Button("Import tags",
                               self.larger_ui_font,
                               self.ImportTagsFromClipboard,
                               padding=self.standard_padding,
                               outline_size=self.standard_outline_size,
                               outline_colour=(255, 255, 255),
                               pressed_background_colour=(200, 200, 200))
        file_import_button = Button("Import from file",
                                    self.larger_ui_font,
                                    self.ImportTagsFromFile,
                                    padding=self.standard_padding,
                                    outline_size=self.standard_outline_size,
                                    outline_colour=(255, 255, 255),
                                    pressed_background_colour=(200, 200, 200))
        export_button = Button("Export tags",
                               self.larger_ui_font,
                               self.ExportTagsToClipboard,
                               padding=self.standard_padding,
                               outline_size=self.standard_outline_size,
                               outline_colour=(255, 255, 255),
                               pressed_background_colour=(200, 200, 200))
        file_export_button = Button("Export to file",
                                    self.larger_ui_font,
                                    self.ExportTagsToFile,
                                    padding=self.standard_padding,
                                    outline_size=self.standard_outline_size,
                                    outline_colour=(255, 255, 255),
                                    pressed_background_colour=(200, 200, 200))
        second_back_button = Button(
            "Back",
            self.larger_ui_font,
            target=self.
            UnloadSecondTagsBar,  # not sure if necessary or can just directly add commands, TODO check
            arguments={
                "TYPE":
                "TRANSITION",
                "TRANSITIONS": [{
                    "ELEMENTS": [
                        ComponentID.TAG_FIRST_BAR.value,
                        ComponentID.TAG_SECOND_BAR.value,
                        ComponentID.TAG_LIST.value
                    ],
                    "STYLE":
                    2,
                    "TIME":
                    1,
                    "DELAY":
                    0,
                    "TYPE":
                    "LEAVING"
                }, {
                    "ELEMENTS": ComponentID.MAIN.value,
                    "STYLE": 2,
                    "TIME": 1,
                    "DELAY": 0,
                    "TYPE": "JOINING"
                }]
            },
            padding=self.wider_padding,
            outline_size=self.standard_outline_size,
            outline_colour=(255, 255, 255),
            pressed_background_colour=(200, 200, 200))
        leave_button = Button(
            " - ",
            self.larger_ui_font,
            self.UnloadSecondTagsBar,
            arguments={
                "TYPE":
                "TRANSITION",
                "TRANSITIONS": [{
                    "ELEMENTS":
                    ComponentID.TAG_SECOND_BAR.value,
                    "STYLE":
                    20,
                    "TIME":
                    1,
                    "DELAY":
                    0,
                    "TYPE":
                    "LEAVING",
                    "POST_ARGS": [{
                        "TYPE": "ACTIVATE",
                        "ID": ComponentID.TAG_FIRST_BAR.value
                    }]
                }]
            },
            padding=MakeElementEqualSize(
                " - ", self.larger_ui_font,
                other_options_button.size - 2 * self.standard_outline_size),
            outline_size=self.standard_outline_size,
            background_colour=(37, 123, 200),
            pressed_background_colour=(37, 123, 200),
            outline_colour=(255, 255, 255),
            text_colour=(255, 255, 255))
        button_container = RegulatedContainer(
            4, 1, inner_padding=self.very_wide_padding)
        button_container.AddElements(import_button, file_import_button,
                                     export_button, file_export_button)
        button_container.position = ScalePosition(Vector2D(0, 0),
                                                  self.tag_second_bar.size,
                                                  Vector2D(0.5, 0.5),
                                                  button_container.size)
        leave_button.position = Vector2D(
            config.settings["window_width"] * 0.919140625,
            button_container.position.y)
        second_back_button.position = back_button.position + top_bar_container.position
        self.tag_second_bar.AddUIElements(second_back_button, button_container,
                                          leave_button)

        self.tag_third_bar = StaticComponent(
            Vector2D(0, 0),
            Vector2D(config.settings["window_width"],
                     config.settings["window_height"] // 7), (50, 50, 50))
        third_back_button = Button("Return",
                                   self.larger_ui_font,
                                   target=self.UnloadThirdTagsBar,
                                   arguments={
                                       "TYPE":
                                       "TRANSITION",
                                       "TRANSITIONS": [{
                                           "ELEMENTS": [
                                               ComponentID.TAG_THIRD_BAR.value,
                                               ComponentID.TAG_LIST.value
                                           ],
                                           "STYLE":
                                           1,
                                           "TIME":
                                           1,
                                           "DELAY":
                                           0,
                                           "TYPE":
                                           "LEAVING"
                                       }, {
                                           "ELEMENTS":
                                           ComponentID.ITEM_ADD.value,
                                           "STYLE":
                                           1,
                                           "TIME":
                                           1,
                                           "DELAY":
                                           0,
                                           "TYPE":
                                           "JOINING"
                                       }, {
                                           "ELEMENTS":
                                           ComponentID.ITEM_ADD_TAGS.value,
                                           "STYLE":
                                           23,
                                           "TIME":
                                           1,
                                           "DELAY":
                                           0,
                                           "TYPE":
                                           "JOINING"
                                       }]
                                   },
                                   padding=self.wider_padding,
                                   outline_size=self.standard_outline_size,
                                   outline_colour=(255, 255, 255),
                                   pressed_background_colour=(200, 200, 200))
        third_bar_container = Container(3, 1, inner_padding=self.large_padding)
        third_bar_container.AddElements(third_back_button,
                                        self.tags_menu_search_entry,
                                        add_new_button)
        third_bar_container.position = ScalePosition(Vector2D(0, 0),
                                                     self.tag_third_bar.size,
                                                     Vector2D(0.5, 0.5),
                                                     third_bar_container.size)
        self.tag_third_bar.AddUIElement(third_bar_container)
        self.tag_third_bar.reset_func = self.ResetTagsMenuFromThirdBar

        self.tag_fourth_bar = StaticComponent(
            Vector2D(0, 0),
            Vector2D(config.settings["window_width"],
                     config.settings["window_height"] // 7), (50, 50, 50))
        fourth_back_button = Button(
            "Return",
            self.larger_ui_font,
            target=self.UnloadFourthTagsBar,
            arguments=[{
                "TYPE": "JOIN",
                "ID": ComponentID.ITEM_ADD_FADE_LAYER.value
            }, {
                "TYPE":
                "SHOW",
                "ID": [
                    ComponentID.ERROR.value, ComponentID.ITEM_ADD.value,
                    ComponentID.ITEM_ADD_TAGS.value
                ]
            }, {
                "TYPE":
                "TRANSITION",
                "TRANSITIONS": [{
                    "ELEMENTS": (self.ChangeFade, 0),
                    "STYLE":
                    5,
                    "TIME":
                    1,
                    "DELAY":
                    0,
                    "TYPE":
                    "JOINING",
                    "POST_ARGS": [{
                        "TYPE": "DEACTIVATE",
                        "ID": ComponentID.ITEM_ADD_FADE_LAYER.value,
                        "CACHE": True
                    }]
                }, {
                    "ELEMENTS": [
                        ComponentID.TAG_FOURTH_BAR.value,
                        ComponentID.TAG_LIST.value
                    ],
                    "STYLE":
                    1,
                    "TIME":
                    1,
                    "DELAY":
                    0,
                    "TYPE":
                    "LEAVING"
                }, {
                    "ELEMENTS":
                    [ComponentID.ITEM_ADD.value, ComponentID.ERROR.value],
                    "STYLE":
                    1,
                    "TIME":
                    1,
                    "DELAY":
                    0,
                    "TYPE":
                    "MOVING"
                }, {
                    "ELEMENTS": ComponentID.ITEM_ADD_TAGS.value,
                    "STYLE": 23,
                    "TIME": 1,
                    "DELAY": 0,
                    "TYPE": "MOVING"
                }]
            }],
            padding=self.wider_padding,
            outline_size=self.standard_outline_size,
            outline_colour=(255, 255, 255),
            pressed_background_colour=(200, 200, 200))
        fourth_bar_container = Container(2,
                                         1,
                                         inner_padding=self.large_padding)
        fourth_bar_container.AddElements(fourth_back_button,
                                         self.tags_menu_search_entry)
        fourth_bar_container.position = ScalePosition(
            Vector2D(0, 0), self.tag_fourth_bar.size, Vector2D(0.5, 0.5),
            fourth_bar_container.size)
        self.tag_fourth_bar.AddUIElement(fourth_bar_container)
        self.tag_fourth_bar.reset_func = self.ResetTagsMenuFromFourthBar

        pos = Vector2D(0, config.settings["window_height"] // 7)
        size = config.settings["window_size"] - pos
        self.tags_list_component = StaticComponent(pos, size, (0, 0, 0, 0))
        self.tags_list_component.additional_height = self.wider_padding.y
        self.excluded_tag_data = []
        self.selected_tag_data = {}
        self.tags = []
        self.original_tags = []
        self.selected_tags = []
        self.tag_text_width = config.settings["window_width"]
        self.tag_text_width -= (config.settings["tags_shown_per_row"] +
                                1) * self.wider_padding.x
        self.tag_text_width /= config.settings["tags_shown_per_row"]
        self.tag_text_width -= 2 * (self.standard_outline_size.x +
                                    self.wider_padding.x)
        tag_button_height = self.standard_ui_font.size("ABCDEFG")[1] + 2 * (
            self.wider_padding.y +
            self.standard_outline_size.y) + self.wider_padding.y
        columns = config.settings["tags_shown_per_row"]
        rows = int(((config.settings["window_height"] * 6) // 7 +
                    self.wider_padding.y) / tag_button_height)
        self.tags_container = ScrollingRegulatedContainer(
            columns,
            rows,
            self.UpdateDisplayedTags,
            edge_padding=self.wider_padding,
            inner_padding=self.wider_padding)
        button_padding = Vector2D(
            MakeElementEqualSize(
                '', self.standard_ui_font,
                Vector2D(self.tag_text_width + 2 * self.wider_padding.x, 0)).x,
            self.wider_padding.y)
        self.tags_buttons = []
        for i in range(columns * rows):
            b = CacheButton('',
                            self.standard_ui_font,
                            target=self.SelectTag,
                            padding=button_padding,
                            outline_size=self.standard_outline_size,
                            background_colour=(100, 100, 100),
                            text_colour=(255, 255, 255),
                            tooltip_info=[None, 0])
            self.tags_buttons.append(b)
        self.tags_container.AddElements(*self.tags_buttons)
        self.tags_list_component.AddUIElement(self.tags_container)

        #changing the main menu transition to the tag menu
        for i in range(rows):
            self.main_tags_button.arguments[3]["TRANSITIONS"].append({
                "ELEMENTS":
                self.tags_buttons[::-1][i * columns:(i + 1) * columns],
                "STYLE":
                21,
                "TIME":
                1,
                "DELAY":
                i * 0.05,
                "TYPE":
                "MOVING"
            })
        self.main_tags_button.arguments[3]["TRANSITIONS"][-1]["POST_ARGS"] = [{
            "TYPE":
            "ACTIVATE",
            "ID":
            ComponentID.TAG_LIST.value
        }]

        tag_fade_layer = StaticComponent(Vector2D(0, 0),
                                         config.settings["window_size"],
                                         (0, 0, 0, 0))
        tag_fade_layer.AddUIElement(self.fade_rectangle)

        window.AddComponent(self.tag_first_bar,
                            ComponentID.TAG_FIRST_BAR.value,
                            active=False,
                            visuals_active=False)
        window.AddComponent(self.tag_second_bar,
                            ComponentID.TAG_SECOND_BAR.value,
                            active=False,
                            visuals_active=False)
        window.AddComponent(self.tag_third_bar,
                            ComponentID.TAG_THIRD_BAR.value,
                            active=False,
                            visuals_active=False)
        window.AddComponent(self.tag_fourth_bar,
                            ComponentID.TAG_FOURTH_BAR.value,
                            active=False,
                            visuals_active=False)
        window.AddComponent(self.tags_list_component,
                            ComponentID.TAG_LIST.value,
                            active=False,
                            visuals_active=False)
        window.AddComponent(tag_fade_layer,
                            ComponentID.TAG_FADE_LAYER.value,
                            active=False,
                            visuals_active=False)

    def UpdateSynonymPositioning(self):
        position = self.standard_padding.copy()
        for b in self.synonym_buttons:
            b.position = position.copy()
            position.y += b.height + self.standard_padding.y
        self.selected_synonyms_component.UpdateMaxHeight()

    def RemoveSynonym(self, synonym):
        debug.Log("Removed a synonym.")
        if synonym in self.synonyms:
            self.synonyms.remove(synonym)
        else:
            return
        for button in self.synonym_buttons:
            if button.arguments == synonym:
                self.synonym_buttons.remove(button)
                self.selected_synonyms_component.RemoveUIElement(button)
                break
        self.UpdateSuggestedSynonyms(exclude=[
            self.tag_name_entry.text
        ])  # in case the removed synonym is one of the suggestions
        self.UpdateSynonymPositioning()

    def GetDisplayText(self, inp, font, max_size):
        if font.size(inp)[0] > max_size:
            text = ''
            j = 0
            while font.size(text + '...')[0] < max_size:
                text += inp[j]
                j += 1
            text = text[:-1] + "..."
        else:
            text = inp
        return text

    def AddSynonym(self, synonym, text='', update_suggested=True):
        debug.Log("Added a synonym.")
        synonym = synonym.lower().strip()
        if synonym in self.synonyms:
            return
        if len(text) == 0:  # i.e. text not known i.e. we need to make it:
            text = self.GetDisplayText(synonym, self.standard_ui_font,
                                       self.suggested_synonym_max_size)
        self.synonyms.append(synonym)
        tooltip = Label(synonym,
                        self.standard_ui_font,
                        padding=self.standard_padding,
                        outline_size=self.standard_outline_size,
                        background_colour=(150, 150, 150),
                        outline_colour=(0, 0, 0)).image
        b = HoverButton(text,
                        self.standard_ui_font,
                        target=self.RemoveSynonym,
                        arguments=synonym,
                        padding=self.standard_padding,
                        outline_size=Vector2D(0, 0),
                        background_colour=(75, 75, 75),
                        text_colour=(200, 200, 200),
                        hover_background_colour=(100, 100, 100),
                        tooltip_info=[tooltip, 0.5])
        self.synonym_buttons.append(b)
        self.selected_synonyms_component.AddUIElement(b)
        self.UpdateSynonymPositioning()
        self.selected_synonyms_component.current_scroll = self.selected_synonyms_component.max_scroll
        if update_suggested:
            self.UpdateSuggestedSynonyms(exclude=[self.tag_name_entry.text])

    def UpdateSuggestedSynonyms(self, exclude=None):
        depth = config.settings["synonym_suggestions_word_depth"]
        current_name = [self.tag_name_entry.text
                        ] if (" " not in self.tag_name_entry.text
                              and len(self.tag_name_entry.text) > 0) else []
        names = self.synonyms + current_name
        words = [name.split("_") for name in names]
        unchecked_synonyms = []  # not checked for if they already exist
        for i in range(len(words)):
            name = words[i]
            if "_".join(name) in unchecked_synonyms or name in words[:i]:
                continue  # a synonym (or name) of that has already been included and we don't want to add them twice
            phrases = []
            word_length = len(name)
            for i in range(word_length):
                end_index = word_length - i
                if end_index > depth:
                    end_index = depth
                for j in range(end_index):
                    end = i + j + 1
                    phrases.append(["_".join(name[i:end]), i, end])
            suggested_info = SQL.GetSuggestedSynonyms(phrases, exclude)
            for s in suggested_info:
                unchecked_synonyms.append("_".join((name[0:s[1]]) + [s[0]] +
                                                   name[s[2]:]))
        synonyms = []  # final list of synonyms
        for synonym in unchecked_synonyms:
            if SQL.FindReplicaTags(
                    synonym
            ) == None:  # i.e. no matches in tag names or synonyms
                synonyms.append(synonym)
        for s in self.synonyms:
            if s in synonyms:
                synonyms.remove(s)

        self.synonym_suggestion_component.ClearUIElements()
        button_width = self.suggested_synonym_max_size
        position = Vector2D(
            (self.synonym_suggestion_component.width -
             self.suggested_synonym_max_size) / 2,
            self.standard_padding.y + self.standard_outline_size.y)
        for i in range(len(synonyms[:50])):
            s = synonyms[i]
            text = self.GetDisplayText(s, self.standard_ui_font,
                                       self.suggested_synonym_max_size)
            b = self.synonym_suggest_buttons[i]
            b.text = text
            b.padding = Vector2D(
                MakeElementEqualSize(text, self.standard_ui_font,
                                     Vector2D(button_width, 0)).x,
                self.standard_padding.y)
            b.top_left_padding = self.standard_padding.copy()
            b.target = self.AddSynonym
            b.arguments = [s, text]
            b.tooltip_image = Label(s,
                                    self.standard_ui_font,
                                    padding=self.standard_padding,
                                    outline_size=self.standard_outline_size,
                                    background_colour=(150, 150, 150),
                                    outline_colour=(0, 0, 0)).image
            b.UpdateImage()
            b.position = position.copy()
            position.y += b.height + self.standard_padding.y
            self.synonym_suggestion_component.AddUIElement(b)

    def CheckTagInfo(self,
                     name,
                     desc,
                     synonyms,
                     error_args,
                     do_notifications,
                     exclude=None):
        if name == '':
            if do_notifications:
                if not self.in_tag_menu:
                    self.AddNotification("You must enter the tag's name.",
                                         display_time=8)
                else:
                    self.DisplayError("You must enter the tag's name.",
                                      *error_args)
            return False
        elif name[0] == '-':
            if do_notifications:
                if not self.in_tag_menu:
                    self.AddNotification(
                        "The first character of the tag's name cannot be a dash.",
                        display_time=8)
                else:
                    self.DisplayError(
                        "The first character of the tag's name cannot be a\ndash.",
                        *error_args)
            return False
        elif " " in name:
            if do_notifications:
                if not self.in_tag_menu:
                    self.AddNotification(
                        "The tag name cannot contain any spaces. Try using underscores instead.",
                        display_time=8)
                else:
                    self.DisplayError(
                        "The tag name cannot contain any spaces. Try\nusing underscores instead.",
                        *error_args)
            return False
        elif name in synonyms:
            if do_notifications:
                if not self.in_tag_menu:
                    self.AddNotification(
                        "The tag cannot have a synonym identical to its name.",
                        display_time=8)
                else:
                    self.DisplayError(
                        "The tag cannot have a synonym identical to its \nname.",
                        *error_args)
            return False
        for char in self.disallowed_characters:
            if char in name:
                if do_notifications:
                    if not self.in_tag_menu:
                        self.AddNotification(
                            f'The tag name cannot contain any {self.disallowed_characters[char]}.',
                            display_time=8)
                    else:
                        self.DisplayError(
                            f'The tag name cannot contain any {self.disallowed_characters[char]}.',
                            *error_args)
                return False
        for phrase in self.disallowed_phrases:
            if phrase == name:
                if do_notifications:
                    if not self.in_tag_menu:
                        self.AddNotification(
                            f'The tag name cannot contain the banned phrase, \'{phrase.upper()}\'.',
                            display_time=8)
                    else:
                        self.DisplayError(
                            f'The tag name cannot contain the banned phrase,\n\'{phrase.upper()}\'.',
                            *error_args)
                return False
        for s in synonyms:
            if " " in s:
                if do_notifications:
                    to_format = s[:75] + ('...' if len(s) > 75 else '')
                    if not self.in_tag_menu:
                        self.AddNotification(
                            "The synonym '{}' contains spaces, which are not allowed."
                            .format(to_format),
                            display_time=8)
                    else:
                        self.DisplayError(
                            "The synonym '{}'\ncontains spaces, which are not allowed."
                            .format(to_format), *error_args)
                return False
            if s[0] == '-':
                if do_notifications:
                    to_format = s[:75] + ('...' if len(s) > 75 else '')
                    if not self.in_tag_menu:
                        self.AddNotification(
                            "The synonym '{}' starts with a dash, which is not allowed."
                            .format(to_format),
                            display_time=8)
                    else:
                        self.DisplayError(
                            "The synonym '{}'\nstarts with a dash, which is not allowed."
                            .format(to_format), *error_args)
                return False
            if len(s) == 0:
                if do_notifications:
                    if not self.in_tag_menu:
                        self.AddNotification(
                            "You cannot have empty text as a synonym.",
                            display_time=8)
                    else:
                        self.DisplayError(
                            "You cannot have empty text as a synonym.",
                            *error_args)
                return False
            for char in self.disallowed_characters:
                if char in s:
                    if do_notifications:
                        to_format = s[:75] + ('...' if len(s) > 75 else '')
                        if not self.in_tag_menu:
                            self.AddNotification(
                                f'The synonym \'{to_format}\' contains {self.disallowed_characters[char]}, which are not allowed.',
                                display_time=8)
                        else:
                            self.DisplayError(
                                f'The synonym \'{to_format}\'\ncontains {self.disallowed_characters[char]}, which are not allowed.',
                                *error_args)
                    return False
            for phrase in self.disallowed_phrases:
                if phrase == s:
                    if do_notifications:
                        to_format = s[:75] + ('...' if len(s) > 75 else '')
                        if not self.in_tag_menu:
                            self.AddNotification(
                                f'The synonym \'{to_format}\' contains the banned phrase \'{phrase.upper()}\', which is not allowed.',
                                display_time=8)
                        else:
                            self.DisplayError(
                                f'The synonym \'{to_format}\'\ncontains the banned phrase \'{phrase.upper()}\',\nwhich is not allowed.',
                                *error_args)
                    return False
        matches = SQL.FindReplicaTags(name, synonyms, exclude=exclude)
        if matches != None:
            if matches[0] == name:
                if matches[2] == "name":
                    if do_notifications:
                        if not self.in_tag_menu:
                            self.AddNotification(
                                "A tag with that name already exists.",
                                display_time=8)
                        else:
                            self.DisplayError(
                                "A tag with that name already exists.",
                                *error_args)
                    return False
                else:
                    if do_notifications:
                        to_format = matches[1][:75] + (
                            '...' if len(matches[1]) > 75 else '')
                        if not self.in_tag_menu:
                            self.AddNotification(
                                "The tag '{}' has a synonym identical to your entered name."
                                .format(to_format),
                                display_time=8)
                        else:
                            self.DisplayError(
                                "The tag '{}'\nhas a synonym identical to your entered name."
                                .format(to_format), *error_args)
                    return False
            elif matches[2] == "name":
                if do_notifications:
                    to_format = matches[1][:75] + (
                        '...' if len(matches[1]) > 75 else '')
                    if not self.in_tag_menu:
                        self.AddNotification(
                            "The tag '{}' has the name of one of your entered synonyms."
                            .format(to_format),
                            display_time=8)
                    else:
                        self.DisplayError(
                            "The tag '{}'\nhas the name of one of your entered synonyms."
                            .format(to_format), *error_args)
                return False
            else:
                if do_notifications:
                    to_format = matches[1][:75] + (
                        '...' if len(matches[1]) > 75 else '')
                    to_format_2 = matches[0][:55] + (
                        '...' if len(matches[0]) > 55 else '')
                    if not self.in_tag_menu:
                        self.AddNotification(
                            "The tag '{}' already has the synonym '{}'.".
                            format(to_format, to_format_2),
                            display_time=8)
                    else:
                        self.DisplayError(
                            "The tag '{}'\nalready has the synonym '{}'.".
                            format(to_format, to_format_2), *error_args)
                return False
        debug.Log("Tag information passed all checks.")
        return True

    def AddNewCategory(self, name):
        index = config.settings[
            "number_of_category_tags"] - self.categories_to_add
        button = self.category_select_buttons[index][0]
        button_text_width = self.larger_ui_font.size(name)[0]
        text = name
        while button_text_width > self.category_text_width:
            text = text[:-1]
            button_text_width = self.larger_ui_font.size(text + '...')[0]
        if text != name:
            text += '...'
        tooltip = Label(name,
                        self.standard_ui_font,
                        padding=self.standard_padding,
                        outline_size=self.standard_outline_size,
                        background_colour=(150, 150, 150),
                        outline_colour=(0, 0, 0)).image
        button.tooltip_image = tooltip
        button.text = text
        button.padding = MakeElementEqualSize(text, self.larger_ui_font,
                                              self.category_button_size)
        button.UpdateImage()
        self.category_list[index] = name
        self.category_select_buttons[index][1] = name
        self.categories_to_add -= 1

    def AttemptAddNewTag(self,
                         name=None,
                         desc=None,
                         synonyms=None,
                         error_args=None,
                         do_transitions=True,
                         do_notifications=True):
        # creation of default arguments in case being done from the CLI
        debug.Log("Attempted to add a new tag.")
        if name == None:
            name = self.tag_name_entry.text.lower().strip()
        if desc == None:
            desc = self.tag_desc_entry.text.strip()
        if synonyms == None:
            synonyms = self.synonyms
        if error_args == None:
            error_args = [
                self.tag_addition_component,
                [
                    ComponentID.TAG_ADD.value,
                    ComponentID.TAG_CHANGE_EXIT.value,
                    ComponentID.TAG_ADD_SUGGESTIONS.value,
                    ComponentID.TAG_ADD_SYNONYMS.value
                ]
            ]
        if not self.CheckTagInfo(name, desc, synonyms, error_args,
                                 do_notifications):
            return False
        SQL.AddTag(name, desc, synonyms)
        if self.categories_to_add > 0:
            self.AddNewCategory(name)
        if do_notifications:
            self.AddNotification("New tag added successfully.")
        ignored = SQL.GetIgnoredTags()
        for item in (([name] + synonyms) if synonyms != None else [name]):
            if item in ignored:
                SQL.RemoveIgnoredTag(name)
        if not do_transitions:
            return True
        self.ExitTagChangeMenu(*self.tag_change_back_button.arguments)
        self.LoadTag(name)
        if not self.in_tag_menu:
            self.AddUnknownAsTag(self.temp_tags, called=2, synonyms=synonyms)
        return True

    def ExitTagChangeMenu(self, *arguments):
        if not self.in_tag_menu:
            self.tag_change_exit_component.AddCommands(
                {
                    "TYPE": "ACTIVATE",
                    "ID": ComponentID.ERROR_FADE_LAYER.value
                }, {
                    "TYPE":
                    "TRANSITION",
                    "TRANSITIONS":
                    [{
                        "ELEMENTS": (self.ChangeFade, 224),
                        "STYLE":
                        8,
                        "TIME":
                        0.5,
                        "DELAY":
                        0,
                        "TYPE":
                        "LEAVING",
                        "POST_ARGS": [{
                            "TYPE": "LEAVE",
                            "ID": ComponentID.ERROR_FADE_LAYER.value
                        }]
                    }, {
                        "ELEMENTS":
                        ComponentID.ERROR.value,
                        "STYLE":
                        9,
                        "TIME":
                        0.5,
                        "DELAY":
                        0,
                        "TYPE":
                        "MOVING",
                        "POST_ARGS": [{
                            "TYPE": "ACTIVATE",
                            "ID": ComponentID.ERROR.value,
                        }]
                    },
                     {
                         "ELEMENTS": [
                             ComponentID.ITEM_ADD_TAGS_ADD.value,
                             ComponentID.ITEM_ADD_TAGS_ADD_SUGGESTIONS.value,
                             ComponentID.ITEM_ADD_TAGS_ADD_SYNONYMS.value
                         ],
                         "STYLE":
                         9,
                         "TIME":
                         0.5,
                         "DELAY":
                         0,
                         "TYPE":
                         "LEAVING"
                     }, {
                         "ELEMENTS": ComponentID.ITEM_ADD_TAGS_ADD_EXIT.value,
                         "STYLE": 10,
                         "TIME": 0.5,
                         "DELAY": 0,
                         "TYPE": "LEAVING"
                     }]
                }, {
                    "TYPE": "EXECUTE",
                    "FUNCTION": self.ChangeFade,
                    "ARGUMENTS": [224],
                    "KWARGUMENTS": {}
                })
            return
        if self.is_adding_tag:
            new_id = ComponentID.TAG_ADD.value
        else:
            new_id = ComponentID.TAG_EDIT.value
        arguments[1]["TRANSITIONS"][1]["ELEMENTS"][0] = new_id
        if self.on_bar == 3:
            new_id = ComponentID.TAG_THIRD_BAR.value
        elif self.on_bar == 2:
            new_id = ComponentID.TAG_SECOND_BAR.value
        else:
            new_id = ComponentID.TAG_FIRST_BAR.value
        current_value = arguments[1]["TRANSITIONS"][1]["POST_ARGS"][0]["ID"]
        arguments[1]["TRANSITIONS"][1]["POST_ARGS"][0]["ID"] = [
            current_value[0], new_id
        ]  # to avoid pointer errors
        self.tag_change_exit_component.AddCommands(*arguments)

    def UpdateSuggestedFromName(self):
        if self.is_adding_tag:
            exclude = None
        else:
            exclude = [self.selected_tag_data["NAME"]]
        self.UpdateSuggestedSynonyms(exclude)

    def ResetTagAdditionMenu(self):
        debug.Log("Reset tag addition / editing menu.")
        self.tag_name_entry.Reset()
        self.tag_desc_entry.Reset()
        self.synonym_entry.Reset()
        self.synonym_buttons = []
        self.synonyms = []
        self.synonym_suggestion_component.ClearUIElements()
        self.selected_synonyms_component.ClearUIElements()
        self.is_adding_tag = True
        self.in_tag_menu = True
        self.tag_addition_component.current_tab_index = None

    def CreateTagAdditionMenu(self, window):
        self.tag_addition_component = StaticComponent(
            Vector2D(config.settings["window_width"] // 2, 0),
            Vector2D(config.settings["window_width"] // 2,
                     config.settings["window_height"]), (50, 50, 50))

        side_bar = Rectangle(
            Vector2D(config.settings["window_width"] // 200,
                     config.settings["window_height"]), (150, 150, 150),
            Vector2D(0, 0))
        top_left_container = Container(
            1,
            4,
            inner_padding=Vector2D(0, config.settings["window_width"] // 60))
        self.tag_name_entry = UnfocusEntry(
            self.medium_large_ui_font,
            config.settings["window_width"] // 5,
            target=self.UpdateSuggestedFromName,
            send_text=False,
            padding=self.standard_padding,
            outline_size=self.standard_outline_size,
            empty_text="Name",
            outline_colour=(150, 150, 150),
            empty_text_colour=(130, 130, 130))
        self.tag_desc_entry = Entry(self.medium_large_ui_font,
                                    config.settings["window_width"] // 5,
                                    padding=self.standard_padding,
                                    outline_size=self.standard_outline_size,
                                    empty_text="Description",
                                    outline_colour=(150, 150, 150),
                                    empty_text_colour=(130, 130, 130))
        button_padding = Vector2D(
            MakeElementEqualSize(
                "Add tag", self.medium_large_ui_font,
                Vector2D(config.settings["window_width"] // 5, 0)).x,
            self.standard_padding.y)
        add_tag_button = Button("Add tag",
                                self.medium_large_ui_font,
                                self.AttemptAddNewTag,
                                padding=button_padding,
                                outline_size=self.standard_outline_size,
                                background_colour=(37, 123, 200),
                                pressed_background_colour=(37, 123, 200),
                                outline_colour=(255, 255, 255),
                                text_colour=(255, 255, 255))
        self.synonym_entry = FunctionalEntry(
            self.medium_large_ui_font,
            config.settings["window_width"] // 5,
            self.AddSynonym,
            padding=self.standard_padding,
            outline_size=self.standard_outline_size,
            empty_text="Enter synonyms",
            outline_colour=(150, 150, 150),
            empty_text_colour=(130, 130, 130))
        top_left_container.AddElements(add_tag_button, self.tag_name_entry,
                                       self.tag_desc_entry, self.synonym_entry)
        top_left_container.position = ScalePosition(
            Vector2D(0, 0), self.tag_addition_component.size,
            Vector2D(0.25, 0.2375 + 1 / 120), top_left_container.size)
        self.tag_addition_component.AddUIElements(side_bar, top_left_container)
        self.tag_addition_component.tab_list = [
            self.tag_name_entry, self.tag_desc_entry, self.synonym_entry
        ]

        size = Vector2D(1.25 * config.settings["window_height"] // 7,
                        config.settings["window_height"] // 7)
        self.tag_change_exit_component = StaticComponent(
            Vector2D(0, 0), size, (150, 150, 150))

        background_size = size - Vector2D(
            config.settings["window_width"] // 400,
            config.settings["window_width"] // 400)
        background_rectangle = Rectangle(background_size, (50, 50, 50))
        self.tag_change_back_button = Button(
            "Back",
            self.larger_ui_font,
            target=self.ExitTagChangeMenu,
            arguments=[
                {
                    "TYPE": "ACTIVATE",
                    "ID": ComponentID.TAG_FADE_LAYER.value
                },
                {
                    "TYPE":
                    "TRANSITION",
                    "TRANSITIONS": [{
                        "ELEMENTS": (self.ChangeFade, 224),
                        "STYLE": 8,
                        "TIME": 0.5,
                        "DELAY": 0,
                        "TYPE": "LEAVING"
                    }, {
                        "ELEMENTS": [
                            ComponentID.TAG_ADD.value,
                            ComponentID.TAG_ADD_SUGGESTIONS.value,
                            ComponentID.TAG_ADD_SYNONYMS.value
                        ],
                        "STYLE":
                        9,
                        "TIME":
                        0.5,
                        "DELAY":
                        0,
                        "TYPE":
                        "LEAVING",
                        "POST_ARGS": [{
                            "TYPE": "ACTIVATE",
                            "ID": [ComponentID.TAG_LIST.value]
                        }]
                    }, {
                        "ELEMENTS": ComponentID.TAG_CHANGE_EXIT.value,
                        "STYLE": 10,
                        "TIME": 0.5,
                        "DELAY": 0,
                        "TYPE": "LEAVING"
                    }]
                },
                {  #  not 100% necessary but might be needed for load menu skips etc. TODO CHECK
                    "TYPE": "EXECUTE",
                    "FUNCTION": self.ChangeFade,
                    "ARGUMENTS": [224],
                    "KWARGUMENTS": {}
                }
            ],
            padding=self.wider_padding,
            outline_size=self.standard_outline_size,
            pressed_background_colour=(200, 200, 200),
            outline_colour=(255, 255, 255))
        self.tag_change_back_button.position = (
            size - self.tag_change_back_button.size) / 2
        self.is_adding_tag = False
        self.in_tag_menu = True

        self.tag_change_exit_component.AddUIElements(
            background_rectangle, self.tag_change_back_button)

        size = Vector2D(config.settings["window_width"] // 5,
                        config.settings["window_height"] * (0.525 - 1 / 60))
        self.synonym_suggestion_component = ScrollComponent(
            Vector2D(0, 0), size, size.y, (75, 75, 75))
        self.synonym_suggestion_component.position = ScalePosition(
            Vector2D(0, 0), config.settings["window_size"],
            Vector2D(0.625, 0.75 + 1 / 60),
            self.synonym_suggestion_component.size)

        self.synonym_suggest_buttons = []
        for i in range(50):
            b = HoverButton('',
                            self.standard_ui_font,
                            target=self.AddSynonym,
                            arguments='',
                            padding=self.standard_padding,
                            outline_size=Vector2D(0, 0),
                            background_colour=(75, 75, 75),
                            text_colour=(200, 200, 200),
                            hover_background_colour=(100, 100, 100),
                            tooltip_info=[None, 0.5])
            self.synonym_suggest_buttons.append(b)
        self.suggested_synonym_max_size = size.x - 2 * (
            self.standard_padding.x + self.wider_padding.x)
        self.synonyms = []

        rect_size = Vector2D(
            config.settings["window_width"] // 5,
            config.settings["window_height"] * (0.975 - 7 / 120))
        size = rect_size - 2 * self.standard_outline_size
        self.selected_synonyms_component = ScrollComponent(
            Vector2D(0, 0),
            size,
            size.y, (75, 75, 75),
            automate_max_scroll=True)
        self.selected_synonyms_component.additional_height = self.standard_padding.y
        self.selected_synonyms_component.UpdateMaxHeight()
        position = Vector2D(config.settings["window_width"] * 0.775,
                            config.settings["window_height"] * 7 / 120)
        self.selected_synonyms_component.position = position
        outline_rectangle = Rectangle(rect_size, (150, 150, 150))
        rect_position = position - self.standard_outline_size
        rect_position.x -= config.settings["window_width"] / 2
        outline_rectangle.position = rect_position
        self.tag_addition_component.AddUIElements(outline_rectangle)
        self.synonym_buttons = []

        self.tag_addition_component.reset_func = self.ResetTagAdditionMenu

        window.AddComponent(self.tag_addition_component,
                            ComponentID.TAG_ADD.value, False, False)
        window.AddComponent(self.tag_change_exit_component,
                            ComponentID.TAG_CHANGE_EXIT.value, False, False)
        window.AddComponent(self.synonym_suggestion_component,
                            ComponentID.TAG_ADD_SUGGESTIONS.value, False,
                            False)
        window.AddComponent(self.selected_synonyms_component,
                            ComponentID.TAG_ADD_SYNONYMS.value, False, False)

    def AttemptUpdateTag(self,
                         old_name=None,
                         old_synonyms=None,
                         name=None,
                         desc=None,
                         synonyms=None,
                         error_args=None,
                         do_transitions=True,
                         do_notifications=True):
        # creation of default arguments in case being done from the CLI
        debug.Log("Attempted to update a tag.")
        if old_name == None:
            old_name = self.selected_tag_data["NAME"]
        if old_synonyms == None:
            old_synonyms = self.selected_tag_data["SYNONYMS"]
        if name == None:
            name = self.tag_name_entry.text.lower().strip()
        if desc == None:
            desc = self.tag_desc_entry.text.strip()
        if synonyms == None:
            synonyms = self.synonyms
        if error_args == None:
            error_args = [
                self.tag_edit_component,
                [
                    ComponentID.TAG_EDIT.value,
                    ComponentID.TAG_CHANGE_EXIT.value,
                    ComponentID.TAG_ADD_SUGGESTIONS.value,
                    ComponentID.TAG_ADD_SYNONYMS.value
                ]
            ]
        if old_name == '':
            if do_notifications:
                if not self.in_tag_menu:
                    self.AddNotification(
                        "You must enter the tag's current name.",
                        display_time=8)
                else:
                    self.DisplayError("You must enter the tag's current name.",
                                      *error_args)
            return False
        if " " in old_name:
            if do_notifications:
                if not self.in_tag_menu:
                    self.AddNotification(
                        "The current tag name cannot contain any spaces. Try using underscores instead.",
                        display_time=8)
                else:
                    self.DisplayError(
                        "The current tag name cannot contain any spaces.\nTry using underscores instead.",
                        *error_args)
            return False
        if not self.CheckTagInfo(name,
                                 desc,
                                 synonyms,
                                 error_args,
                                 do_notifications,
                                 exclude=[old_name]):
            return False
        SQL.UpdateTag(old_name, old_synonyms, name, desc, synonyms)
        self.ReplaceLoadedTag(old_name, name)
        ignored = SQL.GetIgnoredTags()
        for item in (([name] + synonyms) if synonyms != None else [name]):
            if item in ignored:
                SQL.RemoveIgnoredTag(name)
        if do_notifications:
            self.AddNotification("Tag edited successfully.")
        if do_transitions:
            self.ExitTagChangeMenu(*self.tag_change_back_button.arguments)
        return True

    def CreateTagEditMenu(self, window):
        self.tag_edit_component = StaticComponent(
            Vector2D(config.settings["window_width"] // 2, 0),
            Vector2D(config.settings["window_width"] // 2,
                     config.settings["window_height"]), (50, 50, 50))

        side_bar = Rectangle(
            Vector2D(config.settings["window_width"] // 200,
                     config.settings["window_height"]), (150, 150, 150),
            Vector2D(0, 0))
        top_left_container = Container(
            1,
            4,
            inner_padding=Vector2D(0, config.settings["window_width"] // 60))
        button_padding = Vector2D(
            MakeElementEqualSize(
                "Update tag", self.medium_large_ui_font,
                Vector2D(config.settings["window_width"] // 5, 0)).x,
            self.standard_padding.y)
        update_tag_button = Button("Update tag",
                                   self.medium_large_ui_font,
                                   self.AttemptUpdateTag,
                                   padding=button_padding,
                                   outline_size=self.standard_outline_size,
                                   background_colour=(37, 123, 200),
                                   pressed_background_colour=(37, 123, 200),
                                   outline_colour=(255, 255, 255),
                                   text_colour=(255, 255, 255))
        top_left_container.AddElements(update_tag_button, self.tag_name_entry,
                                       self.tag_desc_entry, self.synonym_entry)
        top_left_container.position = ScalePosition(
            Vector2D(0, 0), self.tag_edit_component.size,
            Vector2D(0.25, 0.2375 + 1 / 120), top_left_container.size)
        self.tag_edit_component.AddUIElements(side_bar, top_left_container)

        window.AddComponent(self.tag_edit_component,
                            ComponentID.TAG_EDIT.value, False, False)

    def LoadSecondItemsBar(self, *arguments):
        debug.Log("Opened the extra options bar in the items menu.")
        self.items_first_bar.AddCommands(*arguments)
        self.on_bar = 2

    def UnloadSecondItemsBar(self, *arguments):
        debug.Log("Closed the extra options bar in the items menu.")
        self.items_second_bar.AddCommands(*arguments)
        self.on_bar = 1

    def AttemptItemImport(self, ImportText):
        from base64 import b64encode as EncodeB64
        from json import loads as LoadJSON
        try:
            imported_text = encryption.DecryptTextWithKey(
                EncodeB64(config.settings["key"]), ImportText)
            item_data = LoadJSON(imported_text)
            successful = 0
            failed = []
            for item in item_data:
                success = self.AttemptAddNewItem(*item[0:8], [
                    self.items_second_bar,
                    [ComponentID.ITEM_SECOND_BAR, ComponentID.ITEM_LIST]
                ], False, False)
                if success:
                    successful += 1
                else:
                    failed.append(item[0])
            self.AddNotification(
                "{} items successfully added & {} failed".format(
                    successful, len(failed)),
                display_time=8)
            debug.Log(
                f'Successfully imported {successful} items and failed to import {len(failed)} items.'
            )
            if successful > 0:
                pass  # TODO ADD self.RefreshItems() when added
        except:
            self.AddNotification("Failed to import items")
            debug.Log("Failed to import items.")

    def ImportItemsFromClipboard(self):
        from pyperclip import paste as PasteFromClipboard
        self.AttemptItemImport(PasteFromClipboard().strip())

    def ImportItemsFromFile(self, filename=None):
        try:
            if filename == None:
                if not self.file_dialog_used:
                    self.SetupDefaultFileDialog()
                    self.file_dialog_used = True
                from tkinter.filedialog import askopenfilename as AskOpenFileName
                filename = AskOpenFileName(
                    title="Select a file to import item data from",
                    filetypes=(("CVAL files", "*.CVAL"), ("Text files",
                                                          "*.txt")))
            if filename != '':
                debug.Log(f'Attempted to import items from a file.')
                with open(filename, "r") as f:
                    data = f.read()
                    f.close()
                self.AttemptItemImport(data.strip())
        except FileNotFoundError:
            self.AddNotification("The specified file could not be found")
        except:
            self.AddNotification("An error occurred accessing the file")

    def GetItemExport(self):
        from base64 import b64encode as EncodeB64
        from json import dumps as DumpJSON
        item_data = DumpJSON(SQL.GetAllItemData())
        return encryption.EncryptTextWithKey(EncodeB64(config.settings["key"]),
                                             item_data)

    def ExportItemsToClipboard(self):
        from pyperclip import copy as CopyToClipboard
        CopyToClipboard(self.GetItemExport())
        self.AddNotification("Item data copied to clipboard")

    def ExportItemsToFile(self, filename=None):
        try:
            if filename == None:
                if not self.file_dialog_used:
                    self.SetupDefaultFileDialog()
                    self.file_dialog_used = True
                from tkinter.filedialog import asksaveasfile as AskSaveAsFile
                file_ = AskSaveAsFile(
                    title="Create a file to save item data to",
                    filetypes=(("CVAL files", "*.CVAL"), ("Text files",
                                                          "*.txt")),
                    defaultextension="CVAL")
            else:
                file_ = open(filename, 'w+')
            if file_ != None:
                debug.Log(f'Exported item information to the a file.')
                file_.write(self.GetItemExport())
                file_.close()
                self.AddNotification("Item data successfully exported to file")
        except:
            self.AddNotification("An error occurred accessing the file")

    def ResetItemsMenu(self):
        self.item_tag_search_entry.Reset()
        self.item_desc_search_entry.Reset()
        self.items_first_bar.current_tab_index = None

    def CreateItemsMenu(self, window):
        self.items_first_bar = StaticComponent(
            Vector2D(0, 0),
            Vector2D(config.settings["window_width"],
                     config.settings["window_height"] // 7), (50, 50, 50))
        back_button = Button("Back",
                             self.larger_ui_font,
                             target=self.items_first_bar.AddCommands,
                             arguments={
                                 "TYPE":
                                 "TRANSITION",
                                 "TRANSITIONS": [{
                                     "ELEMENTS":
                                     [ComponentID.ITEM_FIRST_BAR.value],
                                     "STYLE":
                                     1,
                                     "TIME":
                                     1,
                                     "DELAY":
                                     0,
                                     "TYPE":
                                     "LEAVING"
                                 }, {
                                     "ELEMENTS": ComponentID.MAIN.value,
                                     "STYLE": 1,
                                     "TIME": 1,
                                     "DELAY": 0,
                                     "TYPE": "JOINING"
                                 }]
                             },
                             padding=self.wider_padding,
                             outline_size=self.standard_outline_size,
                             outline_colour=(255, 255, 255),
                             pressed_background_colour=(200, 200, 200))
        self.item_tag_search_entry = FunctionalEntry(
            self.larger_ui_font,
            config.settings["window_width"] * 17 // 48,
            print,
            padding=self.wider_padding,
            outline_size=self.standard_outline_size,
            empty_text="Search by tags",
            outline_colour=(255, 255, 255),
            empty_text_colour=(170, 170, 170))
        self.item_desc_search_entry = FunctionalEntry(
            self.larger_ui_font,
            config.settings["window_width"] * 17 // 48,
            print,
            padding=self.wider_padding,
            outline_size=self.standard_outline_size,
            empty_text="Search by description",
            outline_colour=(255, 255, 255),
            empty_text_colour=(170, 170, 170))
        add_new_button = Button(
            "Add new",
            self.larger_ui_font,
            target=self.items_first_bar.AddCommands,
            arguments=[
                {
                    "TYPE":
                    "TRANSITION",
                    "TRANSITIONS": [
                        {
                            "ELEMENTS": ComponentID.ITEM_ADD.value,
                            "STYLE": 2,
                            "TIME": 1,
                            "DELAY": 0,
                            "TYPE": "JOINING"
                        },
                        {
                            "ELEMENTS":
                            ComponentID.ITEM_ADD_TAGS.value,
                            "STYLE":
                            22,
                            "TIME":
                            1,
                            "DELAY":
                            0,
                            "TYPE":
                            "JOINING",
                            "POST_ARGS": [
                                {
                                    "TYPE": "EXECUTE",
                                    "FUNCTION": self.
                                    ResetItemsMenu,  # only performed when adding a new tag, not when viewing and editing/updating a tag
                                    "ARGUMENTS": [],
                                    "KWARGUMENTS": {}
                                },
                                {
                                    "TYPE": "DEACTIVATE",
                                    "ID": [ComponentID.ITEM_FIRST_BAR.value
                                           ],  # to add second bar and list
                                    "CACHE": True
                                },
                                {
                                    "TYPE": "HIDE",
                                    "ID": [ComponentID.ITEM_FIRST_BAR.value
                                           ]  # to add second bar and list
                                }
                            ]
                        }
                    ]
                },
                {
                    "TYPE": "DEACTIVATE",
                    "ID": [ComponentID.ITEM_FIRST_BAR.value
                           ],  # to add second bar and list
                }
            ],
            padding=self.wider_padding,
            outline_size=self.standard_outline_size,
            background_colour=(37, 123, 200),
            pressed_background_colour=(37, 123, 200),
            outline_colour=(255, 255, 255),
            text_colour=(255, 255, 255))
        other_options_button = Button(
            " + ",
            self.larger_ui_font,
            target=self.LoadSecondItemsBar,
            arguments=[{
                "TYPE": "DEACTIVATE",
                "ID": ComponentID.ITEM_FIRST_BAR.value,
                "CACHE": True
            }, {
                "TYPE":
                "TRANSITION",
                "TRANSITIONS": [{
                    "ELEMENTS": ComponentID.ITEM_SECOND_BAR.value,
                    "STYLE": 19,
                    "TIME": 1,
                    "DELAY": 0,
                    "TYPE": "JOINING"
                }]
            }],
            padding=self.wider_padding,
            outline_size=self.standard_outline_size,
            background_colour=(37, 123, 200),
            pressed_background_colour=(37, 123, 200),
            outline_colour=(255, 255, 255),
            text_colour=(255, 255, 255))
        first_bar_container = Container(5, 1, inner_padding=self.wider_padding)
        first_bar_container.AddElements(back_button,
                                        self.item_tag_search_entry,
                                        self.item_desc_search_entry,
                                        add_new_button, other_options_button)
        first_bar_container.position = ScalePosition(Vector2D(0, 0),
                                                     self.items_first_bar.size,
                                                     Vector2D(0.5, 0.5),
                                                     first_bar_container.size)
        self.items_first_bar.AddUIElement(first_bar_container)
        self.items_first_bar.tab_list = [
            self.item_tag_search_entry, self.item_desc_search_entry
        ]
        self.items_first_bar.reset_func = self.ResetItemsMenu

        self.items_second_bar = StaticComponent(
            Vector2D(0, 0),
            Vector2D(config.settings["window_width"],
                     config.settings["window_height"] // 7), (50, 50, 50))
        import_button = Button("Import items",
                               self.larger_ui_font,
                               self.ImportItemsFromClipboard,
                               padding=self.standard_padding,
                               outline_size=self.standard_outline_size,
                               outline_colour=(255, 255, 255),
                               pressed_background_colour=(200, 200, 200))
        file_import_button = Button("Import from file",
                                    self.larger_ui_font,
                                    self.ImportItemsFromFile,
                                    padding=self.standard_padding,
                                    outline_size=self.standard_outline_size,
                                    outline_colour=(255, 255, 255),
                                    pressed_background_colour=(200, 200, 200))
        export_button = Button("Export items",
                               self.larger_ui_font,
                               self.ExportItemsToClipboard,
                               padding=self.standard_padding,
                               outline_size=self.standard_outline_size,
                               outline_colour=(255, 255, 255),
                               pressed_background_colour=(200, 200, 200))
        file_export_button = Button("Export to file",
                                    self.larger_ui_font,
                                    self.ExportItemsToFile,
                                    padding=self.standard_padding,
                                    outline_size=self.standard_outline_size,
                                    outline_colour=(255, 255, 255),
                                    pressed_background_colour=(200, 200, 200))
        second_back_button = Button(
            "Back",
            self.larger_ui_font,
            target=self.UnloadSecondItemsBar,
            arguments={
                "TYPE":
                "TRANSITION",
                "TRANSITIONS": [
                    {
                        "ELEMENTS": [
                            ComponentID.ITEM_FIRST_BAR.value,
                            ComponentID.ITEM_SECOND_BAR.value
                        ],  # todo add ComponentID.ITEM_LIST.value
                        "STYLE":
                        1,
                        "TIME":
                        1,
                        "DELAY":
                        0,
                        "TYPE":
                        "LEAVING"
                    },
                    {
                        "ELEMENTS": ComponentID.MAIN.value,
                        "STYLE": 1,
                        "TIME": 1,
                        "DELAY": 0,
                        "TYPE": "JOINING"
                    }
                ]
            },
            padding=self.wider_padding,
            outline_size=self.standard_outline_size,
            outline_colour=(255, 255, 255),
            pressed_background_colour=(200, 200, 200))
        leave_button = Button(
            " - ",
            self.larger_ui_font,
            self.UnloadSecondItemsBar,
            arguments={
                "TYPE":
                "TRANSITION",
                "TRANSITIONS": [{
                    "ELEMENTS":
                    ComponentID.ITEM_SECOND_BAR.value,
                    "STYLE":
                    20,
                    "TIME":
                    1,
                    "DELAY":
                    0,
                    "TYPE":
                    "LEAVING",
                    "POST_ARGS": [{
                        "TYPE": "ACTIVATE",
                        "ID": ComponentID.ITEM_FIRST_BAR.value
                    }]
                }]
            },
            padding=MakeElementEqualSize(
                " - ", self.larger_ui_font,
                other_options_button.size - 2 * self.standard_outline_size),
            outline_size=self.standard_outline_size,
            background_colour=(37, 123, 200),
            pressed_background_colour=(37, 123, 200),
            outline_colour=(255, 255, 255),
            text_colour=(255, 255, 255))
        button_container = RegulatedContainer(
            4, 1, inner_padding=self.very_wide_padding)
        button_container.AddElements(import_button, file_import_button,
                                     export_button, file_export_button)
        button_container.position = ScalePosition(Vector2D(0, 0),
                                                  self.items_second_bar.size,
                                                  Vector2D(0.5, 0.5),
                                                  button_container.size)
        leave_button.position = Vector2D(
            config.settings["window_width"] * 0.93671875,
            config.settings["window_height"] * 21.5 // 720)
        second_back_button.position = back_button.position + first_bar_container.position
        self.items_second_bar.AddUIElements(second_back_button,
                                            button_container, leave_button)

        window.AddComponent(self.items_first_bar,
                            ComponentID.ITEM_FIRST_BAR.value, False, False)
        window.AddComponent(self.items_second_bar,
                            ComponentID.ITEM_SECOND_BAR.value, False, False)

    def UpdateCategoryButton(self, pressed, index):
        if pressed:
            if self.category_select_buttons[index][1] == 'N/A':
                self.category_select_buttons[index][0].pressed = False
            for i, button_data in enumerate(self.category_select_buttons):
                if i != index:
                    button_data[0].pressed = False

    def UpdateImportedItemTags(self, tags):
        for tag in tags:
            if tag not in self.selected_tags:
                if tag in self.category_list:
                    for b in self.category_select_buttons:
                        if tag == b[1]:
                            b[0].pressed = True
                        else:
                            b[0].pressed = False
                    continue
                self.selected_tags.append(tag)
                self.AddItemTag(tag)

    def SkipAllTagNotifications(self):
        self.error_component.AddCommands(*self.item_fade_exit_arguments)
        self.error_component.AddCommand(self.error_exit_argument)

    def SkipOneTagNotification(self, unknown_tags, called=1):
        if called == 1:
            if len(unknown_tags) == 1:
                self.error_component.AddCommands(
                    *self.item_fade_exit_arguments)
            self.error_exit_argument["TRANSITIONS"][0]["POST_ARGS"].append({
                "TYPE":
                "EXECUTE",
                "FUNCTION":
                self.SkipOneTagNotification,
                "ARGUMENTS": [unknown_tags],
                "KWARGUMENTS": {
                    "called": 2
                }
            })
            self.error_component.AddCommand(self.error_exit_argument)
            self.import_ignore_list.append(unknown_tags[0])
            if controls["keys_pressed"][
                    304]:  # if shift pressed, add to the ignore list.
                SQL.AddIgnoredTag(unknown_tags[0])
        else:
            unknown_tags = unknown_tags[1:]
            if len(unknown_tags) > 0:
                self.HandleUnknownItemTags(unknown_tags)

    def AddUnknownAsTag(self, unknown_tags, called=1, synonyms=None):
        if called == 1:
            self.ResetTagAdditionMenu()
            self.tag_name_entry.text = unknown_tags[0]
            self.tag_name_entry.UpdateText()
            self.in_tag_menu = False
            self.error_component.AddCommands(
                {
                    "TYPE": "JOIN",
                    "ID": ComponentID.ERROR_FADE_LAYER.value
                }, {
                    "TYPE": "SHOW",
                    "ID": ComponentID.ITEM_ADD_TAGS_ADD.value
                }, {
                    "TYPE":
                    "DEACTIVATE",
                    "ID": [
                        ComponentID.ERROR.value,
                        ComponentID.ITEM_ADD_TAGS_ADD.value
                    ],
                    "CACHE":
                    True
                }, {
                    "TYPE": "MOVE",
                    "ID": ComponentID.ITEM_ADD_TAGS_ADD.value,
                    "POSITION": Vector2D(config.settings["window_width"], 0)
                }, {
                    "TYPE":
                    "TRANSITION",
                    "TRANSITIONS": [{
                        "ELEMENTS": (self.ChangeFade, 0),
                        "STYLE":
                        5,
                        "TIME":
                        0.5,
                        "DELAY":
                        0,
                        "TYPE":
                        "JOINING",
                        "POST_ARGS": [{
                            "TYPE": "DEACTIVATE",
                            "ID": ComponentID.ERROR_FADE_LAYER.value,
                            "CACHE": True
                        }]
                    }, {
                        "ELEMENTS": ComponentID.ERROR.value,
                        "STYLE": 6,
                        "TIME": 0.5,
                        "DELAY": 0,
                        "TYPE": "MOVING"
                    }, {
                        "ELEMENTS":
                        ComponentID.ITEM_ADD_TAGS_ADD.value,
                        "STYLE":
                        6,
                        "TIME":
                        0.5,
                        "DELAY":
                        0,
                        "TYPE":
                        "MOVING",
                        "POST_ARGS": [{
                            "TYPE": "ACTIVATE",
                            "ID": ComponentID.ITEM_ADD_TAGS_ADD.value
                        }]
                    }, {
                        "ELEMENTS":
                        ComponentID.ITEM_ADD_TAGS_ADD_EXIT.value,
                        "STYLE":
                        11,
                        "TIME":
                        1.25,
                        "DELAY":
                        0.5,
                        "TYPE":
                        "JOINING"
                    }, {
                        "ELEMENTS":
                        ComponentID.ITEM_ADD_TAGS_ADD_SUGGESTIONS.value,
                        "STYLE":
                        12,
                        "TIME":
                        0.5,
                        "DELAY":
                        0,
                        "TYPE":
                        "JOINING"
                    }, {
                        "ELEMENTS":
                        ComponentID.ITEM_ADD_TAGS_ADD_SYNONYMS.value,
                        "STYLE":
                        13,
                        "TIME":
                        0.5,
                        "DELAY":
                        0,
                        "TYPE":
                        "JOINING"
                    }]
                }, {
                    "TYPE": "EXECUTE",
                    "FUNCTION": self.ChangeFade,
                    "ARGUMENTS": [0],
                    "KWARGUMENTS": {}
                })
            self.temp_tags = unknown_tags
        elif called == 2:
            if synonyms != None:
                to_remove = []
                for s in synonyms:
                    if s in unknown_tags:
                        to_remove.append(s)
                for item in to_remove:
                    unknown_tags.remove(item)
            if len(unknown_tags) <= 1:
                self.error_component.AddCommands(
                    *self.item_fade_exit_arguments)
            self.error_exit_argument["TRANSITIONS"][0]["POST_ARGS"].append({
                "TYPE":
                "EXECUTE",
                "FUNCTION":
                self.AddUnknownAsTag,
                "ARGUMENTS": [unknown_tags],
                "KWARGUMENTS": {
                    "called": 3
                }
            })
            self.error_component.AddCommand(self.error_exit_argument)
            self.UpdateImportedItemTags([self.tags[-1][0]])
        else:
            if len(unknown_tags) != 0:
                unknown_tags = unknown_tags[1:]
            if len(unknown_tags) > 0:
                self.HandleUnknownItemTags(unknown_tags)

    def AddUnknownAsSynonym(self,
                            unknown_tags,
                            tag_name=None,
                            updated=False,
                            called=1):
        if called == 1:
            debug.Log(
                "Opened the tag selection menu for adding tags to items.")
            # we must store self.selected_tags as they will be overwritten when the menu is loaded
            self.temp_tags = [self.selected_tags]
            self.LoadFourthTagsBar(
                {
                    "TYPE": "HIDE",
                    "ID": ComponentID.ITEM_FIRST_BAR.value  # TODO update
                },
                {
                    "TYPE": "JOIN",
                    "ID": ComponentID.TAG_LIST.value,
                },
                {
                    "TYPE": "MOVE",
                    "ID": ComponentID.TAG_LIST.value,
                    "POSITION": Vector2D(0,
                                         config.settings["window_height"] // 7)
                },
                {
                    "TYPE": "DEACTIVATE",
                    "ID": ComponentID.TAG_LIST.value,
                    "CACHE": False
                },
                {
                    "TYPE":
                    "TRANSITION",
                    "TRANSITIONS": [{
                        "ELEMENTS": [
                            ComponentID.ITEM_ADD.value,
                            ComponentID.ITEM_ADD_TAGS.value
                        ],
                        "STYLE":
                        2,
                        "TIME":
                        1,
                        "DELAY":
                        0,
                        "TYPE":
                        "LEAVING"
                    }, {
                        "ELEMENTS": ComponentID.TAG_FOURTH_BAR.value,
                        "STYLE": 7,
                        "TIME": 0.5,
                        "DELAY": 0.9,
                        "TYPE": "JOINING"
                    }, *self.tag_button_movement_arguments]
                })
            self.error_component.AddCommands(
                {
                    "TYPE": "ACTIVATE",
                    "ID": ComponentID.ITEM_ADD_FADE_LAYER.value
                }, {
                    "TYPE":
                    "TRANSITION",
                    "TRANSITIONS": [{
                        "ELEMENTS": (self.ChangeFade, 224),
                        "STYLE":
                        8,
                        "TIME":
                        1,
                        "DELAY":
                        0,
                        "TYPE":
                        "LEAVING",
                        "POST_ARGS":
                        [{
                            "TYPE": "LEAVE",
                            "ID": ComponentID.ITEM_ADD_FADE_LAYER.value,
                        }]
                    }, {
                        "ELEMENTS":
                        ComponentID.ERROR.value,
                        "STYLE":
                        2,
                        "TIME":
                        1,
                        "DELAY":
                        0,
                        "TYPE":
                        "MOVING",
                        "POST_ARGS": [{
                            "TYPE": "HIDE",
                            "ID": ComponentID.ERROR.value
                        }]
                    }]
                }, {
                    "TYPE": "EXECUTE",
                    "FUNCTION": self.ChangeFade,
                    "ARGUMENTS": [224],
                    "KWARGUMENTS": {}
                })
            self.temp_tags.append(unknown_tags)
        elif called == 2:
            self.tag_fourth_bar.AddCommands(
                {
                    "TYPE": "JOIN",
                    "ID": ComponentID.ITEM_ADD_FADE_LAYER.value
                }, {
                    "TYPE":
                    "SHOW",
                    "ID": [
                        ComponentID.ERROR.value, ComponentID.ITEM_ADD.value,
                        ComponentID.ITEM_ADD_TAGS.value
                    ]
                }, {
                    "TYPE":
                    "TRANSITION",
                    "TRANSITIONS": [{
                        "ELEMENTS": (self.ChangeFade, 0),
                        "STYLE":
                        5,
                        "TIME":
                        1,
                        "DELAY":
                        0,
                        "TYPE":
                        "JOINING",
                        "POST_ARGS": [{
                            "TYPE": "DEACTIVATE",
                            "ID": ComponentID.ITEM_ADD_FADE_LAYER.value,
                            "CACHE": True
                        }]
                    }, {
                        "ELEMENTS": [
                            ComponentID.TAG_FOURTH_BAR.value,
                            ComponentID.TAG_LIST.value
                        ],
                        "STYLE":
                        1,
                        "TIME":
                        1,
                        "DELAY":
                        0,
                        "TYPE":
                        "LEAVING"
                    }, {
                        "ELEMENTS":
                        [ComponentID.ITEM_ADD.value, ComponentID.ERROR.value],
                        "STYLE":
                        1,
                        "TIME":
                        1,
                        "DELAY":
                        0,
                        "TYPE":
                        "MOVING"
                    }, {
                        "ELEMENTS": ComponentID.ITEM_ADD_TAGS.value,
                        "STYLE": 23,
                        "TIME": 1,
                        "DELAY": 0,
                        "TYPE": "MOVING"
                    }]
                })
            if len(unknown_tags) == 1:
                self.error_component.AddCommands(
                    *self.item_fade_exit_arguments)
            self.error_exit_argument["TRANSITIONS"][0]["POST_ARGS"].append({
                "TYPE":
                "EXECUTE",
                "FUNCTION":
                self.AddUnknownAsTag,
                "ARGUMENTS": [unknown_tags],
                "KWARGUMENTS": {
                    "called": 3
                }
            })
            self.error_component.AddCommand(self.error_exit_argument)
            self.selected_tags = self.temp_tags[0]
            if updated:
                self.UpdateImportedItemTags([tag_name])
        else:
            unknown_tags = unknown_tags[1:]
            if len(unknown_tags) > 0:
                self.HandleUnknownItemTags(unknown_tags)

    def HandleUnknownItemTags(self, unknown_tags):
        # TODO REMOVE: self.notification_skip_all_button self.notification_skip_one_button self.notification_add_as_new_button self.notification_add_as_synonym_button
        self.notification_skip_all_button.text = f'Skip all ({len(unknown_tags)})'
        self.notification_skip_all_button.UpdateImage()
        buttons = [
            self.notification_skip_all_button,
            self.notification_skip_one_button,
            self.notification_add_as_new_button,
            self.notification_add_as_synonym_button
        ]

        total_width = sum([b.width for b in buttons])
        total_width += 3 * self.very_wide_padding.x
        pos = (self.error_component.width - total_width) / 2
        for b in buttons:
            b.position.x = pos
            pos += b.width + self.very_wide_padding.x

        tag = unknown_tags[0]
        for button in buttons[1:]:
            button.arguments = [unknown_tags]
        formatted = tag if len(tag) < 75 else (tag[:75] + '...')
        text = f'The entered tag \'{formatted}\'\ndoes not currently exist.'
        active_ids = [
            ComponentID.ITEM_ADD.value, ComponentID.ITEM_ADD_TAGS.value
        ]
        self.item_tags_component.AddCommands(*self.item_fade_arguments)
        self.DisplayError(text,
                          self.item_tags_component,
                          active_ids,
                          title="IMPORT PROBLEM",
                          alternate_buttons=buttons)

    def AttemptAddItemTag(self, new_tag):
        debug.Log("Attempted to manually enter an item tag.")
        new_tag = new_tag.strip().lower()
        new_tag = "_".join(new_tag.split(" "))
        tag_names = SQL.GetTagNames(
        )  # TODO edit and make more efficient? Good enough for now though
        if new_tag not in tag_names:
            matches = SQL.FindReplicaTags(new_tag)
            if matches == None:
                self.HandleUnknownItemTags([new_tag])
            else:
                tag_name = matches[1]
                self.UpdateImportedItemTags([tag_name])
        else:
            self.UpdateImportedItemTags([new_tag])

    def ImportItemTags(self):
        from pyperclip import paste as PasteFromClipboard
        debug.Log("Attempted to import item tags from clipboard.")
        self.item_added_tags = FormatImportTags(PasteFromClipboard())
        if self.item_added_tags == None:
            self.AddNotification("Unable to load any tag data from clipboard",
                                 display_time=8)
            return
        debug.Log("Data in clipboard was valid for item tag imports.")
        tag_names = SQL.GetTagNames()
        permanent_ignored = SQL.GetIgnoredTags()
        known_tags = []
        unknown_tags = []
        for tag in self.item_added_tags:
            if tag in self.import_ignore_list:
                continue
            if tag not in tag_names:
                matches = SQL.FindReplicaTags(tag)
                if matches == None:
                    if tag not in unknown_tags:
                        if tag in permanent_ignored:
                            continue
                        unknown_tags.append(tag)
                else:
                    tag_name = matches[1]
                    if tag_name not in known_tags:
                        known_tags.append(tag_name)
            elif tag not in known_tags:
                known_tags.append(tag)
        if len(unknown_tags) == 0:
            self.AddNotification("Imported all tag data successfully",
                                 display_time=8)
            if len(known_tags) > 0:
                self.UpdateImportedItemTags(known_tags)
        else:
            self.AddNotification(
                "Imported some tag data - confirmation needed", display_time=8)
            if len(known_tags) > 0:
                self.UpdateImportedItemTags(known_tags)
            self.HandleUnknownItemTags(unknown_tags)

    def CheckItemInfo(self, text, rating, tags, error_args, do_notifications):
        if text == '':
            if do_notifications:
                self.DisplayError("You must enter the item's text.",
                                  *error_args)
            return False
        elif " " in text:
            if do_notifications:
                self.DisplayError("The item text cannot contain any spaces.",
                                  *error_args)
            return False
        elif int(rating) != rating:
            if do_notifications:
                self.DisplayError("The item rating must be a whole number.",
                                  *error_args)
            return False
        elif rating < 0 or rating > 10:
            if do_notifications:
                self.DisplayError("The item rating must be between 0 and 10.",
                                  *error_args)
            return False
        all_items = SQL.GetItemNames()
        if text in all_items:
            if do_notifications:
                self.DisplayError(
                    "An item with that item text already exists.", *error_args)
            return False
        current_tags = SQL.GetTagNames()
        for tag in tags:
            if tag not in current_tags:
                if do_notifications:
                    to_format = tag if len(tag) < 75 else (tag[:75] + '...')
                    self.DisplayError(
                        f'The tag \'{to_format}\'\ndoes not exist.',
                        *error_args)
                return False
        return True

    def AttemptAddNewItem(self,
                          text=None,
                          desc=None,
                          times_served=None,
                          time_added=None,
                          time_last_updated=None,
                          score=None,
                          rating=None,
                          tags=None,
                          error_args=None,
                          do_transitions=True,
                          do_notifications=True):
        debug.Log("Attempted to add a new item.")
        # creation of default arguments in case being done from the CLI
        if text == None:
            text = self.item_text_entry.text.lower().strip()
        if desc == None:
            desc = self.item_desc_entry.text.strip()
        if times_served == None:
            times_served = 0
        if time_added == None:
            time_added = CurrentTime()
        if time_last_updated == None:
            time_last_updated = time_added
        if score == None:
            score = 0
        if rating == None:
            rating = self.item_rating_bar.rating
        if error_args == None:
            error_args = [
                self.item_add_component,
                [ComponentID.ITEM_ADD.value, ComponentID.ITEM_ADD_TAGS.value]
            ]
        if tags == None:
            button_pressed = False
            for b in self.category_select_buttons:
                if b[0].pressed:
                    button_pressed = True
                    tags = [b[1]]
                    break
            if not button_pressed:
                if do_notifications:
                    self.DisplayError('No item category has been selected.',
                                      *error_args)
                return False
            tags += self.selected_tags
        if not self.CheckItemInfo(text, rating, tags, error_args,
                                  do_notifications):
            return False
        SQL.AddItem(text, desc, times_served, time_added, time_last_updated,
                    score, rating, tags)
        if do_notifications:
            self.AddNotification("New item added successfully.")
        if not do_transitions:
            return True
        self.ExitItemChangeMenu(*self.item_change_back_button.arguments)
        # TODO add a self.LoadItem() etc. call here when that is implemented
        return True

    def ExitItemChangeMenu(self, *arguments):
        # TODO change; this will be more complex later when the option to view items is added.
        self.item_add_component.AddCommands(*arguments)

    def ResetItemChangeMenu(self):
        self.item_rating_bar.rating = 0
        self.item_rating_bar.UpdateImage()
        self.item_text_entry.Reset()
        self.item_desc_entry.Reset()
        self.manual_item_tag_search.Reset()
        self.selected_tags = []
        self.item_tags_buttons = []
        self.item_tags_component.ClearUIElements()
        for button in self.category_select_buttons:
            button[0].pressed = False
        self.item_add_component.current_tab_index = None

    def CreateItemChangeMenu(self, window):
        self.item_add_component = StaticComponent(
            Vector2D(0, 0), config.settings["window_size"], (50, 50, 50))
        base_star = pygame.image.load(
            "gui\\images\\star_filled_light_grey.png")
        base_star.convert_alpha()
        alternate_star = pygame.image.load(
            "gui\\images\\star_filled_white.png")
        alternate_star.convert_alpha()
        self.item_change_back_button = Button(
            "Back",
            self.larger_ui_font,
            target=self.ExitItemChangeMenu,
            arguments=[
                {
                    "TYPE": "SHOW",
                    "ID": [ComponentID.ITEM_FIRST_BAR.value
                           ]  # to add second bar and list
                },
                {
                    "TYPE":
                    "TRANSITION",
                    "TRANSITIONS": [{
                        "ELEMENTS": [
                            ComponentID.ITEM_ADD.value,
                            ComponentID.ITEM_ADD_TAGS.value
                        ],
                        "STYLE":
                        1,
                        "TIME":
                        1,
                        "DELAY":
                        0,
                        "TYPE":
                        "LEAVING",
                        "POST_ARGS": [
                            {
                                "TYPE": "ACTIVATE",
                                "ID": [ComponentID.ITEM_FIRST_BAR.value
                                       ]  # to add second bar and list
                            },
                            {
                                "TYPE": "EXECUTE",
                                "FUNCTION": self.ResetItemChangeMenu,
                                "ARGUMENTS": [],
                                "KWARGUMENTS": {}
                            }
                        ]
                    }]
                },
            ],
            padding=self.wider_padding,
            outline_size=self.standard_outline_size,
            background_colour=(100, 100, 100),
            pressed_background_colour=(100, 100, 100),
            outline_colour=(150, 150, 150),
            text_colour=(255, 255, 255))
        self.item_change_back_button.position = self.large_padding.copy()
        update_item_button = Button("Update item",
                                    self.larger_ui_font,
                                    target=print,
                                    arguments=None,
                                    padding=self.wider_padding,
                                    outline_size=self.standard_outline_size,
                                    background_colour=(37, 123, 200),
                                    pressed_background_colour=(37, 123, 200),
                                    outline_colour=(255, 255, 255),
                                    text_colour=(255, 255, 255))
        update_item_button.position = self.large_padding.copy()
        update_item_button.position.x += self.item_change_back_button.width + self.large_padding.x
        add_item_button = Button(
            "Add item",
            self.larger_ui_font,
            target=self.AttemptAddNewItem,
            arguments=None,
            padding=MakeElementEqualSize("Add item", self.larger_ui_font,
                                         update_item_button.size) -
            self.standard_outline_size,
            outline_size=self.standard_outline_size,
            background_colour=(37, 123, 200),
            pressed_background_colour=(37, 123, 200),
            outline_colour=(255, 255, 255),
            text_colour=(255, 255, 255))
        add_item_button.position = update_item_button.position.copy()
        self.remove_item_button = Button(
            "Remove item",
            self.larger_ui_font,
            target=print,
            arguments=None,
            padding=self.wider_padding,
            outline_size=self.standard_outline_size,
            background_colour=(192, 57, 43),
            pressed_background_colour=(192, 57, 43),
            outline_colour=(242, 107, 93),
            text_colour=(255, 255, 255)
        )  # Defined here for positioning, actually used in the item edit menu.
        self.remove_item_button.position = update_item_button.position.copy()
        self.remove_item_button.position.x += update_item_button.width + self.large_padding.x
        rating_bar_pos = self.remove_item_button.position.copy()
        rating_bar_pos.x += self.remove_item_button.width + self.large_padding.x
        rating_bar_size = Vector2D(
            config.settings["window_width"] - rating_bar_pos.x -
            self.large_padding.x,
            self.larger_ui_font.size("ABCDEFGH")[1] + 2 *
            (self.wider_padding.y + self.standard_outline_size.y))
        self.item_rating_bar = RatingsBar(
            base_star,
            alternate_star,
            rating_bar_size,
            min_rating=0,
            max_rating=10,
            padding=Vector2D(self.font_size * 4 // 5, self.font_size // 5),
            outline_size=self.standard_outline_size,
            outline_colour=(150, 150, 150),
            background_colour=(100, 100, 100))
        self.item_rating_bar.position = rating_bar_pos.copy()
        category_tags = SQL.GetFirstTags(
            config.settings["number_of_category_tags"])
        tag_width = config.settings["window_width"] - (
            config.settings["number_of_category_tags"] +
            1) * self.very_wide_padding.x
        tag_width /= config.settings["number_of_category_tags"]
        self.category_text_width = tag_width - 2 * (
            self.standard_outline_size.x + self.wider_padding.x)
        self.category_button_size = Vector2D(
            tag_width, self.item_change_back_button.height)
        self.category_button_size -= 2 * self.standard_outline_size
        category_buttons = Container(
            config.settings["number_of_category_tags"],
            1,
            edge_padding=Vector2D(0, 0),
            inner_padding=self.very_wide_padding)
        self.category_select_buttons = []
        self.category_list = []
        self.categories_to_add = config.settings[
            "number_of_category_tags"] - len(category_tags)
        if self.categories_to_add > 0:
            for i in range(self.categories_to_add):
                category_tags.append('N/A')
        for i, tag in enumerate(category_tags):
            button_text_width = self.larger_ui_font.size(tag)[0]
            text = tag
            while button_text_width > self.category_text_width:
                text = text[:-1]
                button_text_width = self.larger_ui_font.size(text + '...')[0]
            if text != tag:
                text += '...'
            tooltip = Label(tag,
                            self.standard_ui_font,
                            padding=self.standard_padding,
                            outline_size=self.standard_outline_size,
                            background_colour=(150, 150, 150),
                            outline_colour=(0, 0, 0)).image
            b = CheckButton(text,
                            self.larger_ui_font,
                            target=self.UpdateCategoryButton,
                            arguments=i,
                            padding=MakeElementEqualSize(
                                text, self.larger_ui_font,
                                self.category_button_size),
                            outline_size=self.standard_outline_size,
                            background_colour=(100, 100, 100),
                            outline_colour=(150, 150, 150),
                            text_colour=(255, 255, 255),
                            tooltip_info=[tooltip, 0.5])
            category_buttons.AddElement(b)
            self.category_select_buttons.append([b, tag])
            self.category_list.append(tag)
        category_buttons.position = ScalePosition(Vector2D(0, 0),
                                                  self.item_add_component.size,
                                                  Vector2D(0.5, 0),
                                                  category_buttons.size)
        category_buttons.position.y = self.item_change_back_button.position.y + self.item_change_back_button.height + self.large_padding.y
        self.item_text_entry = Entry(self.medium_large_ui_font,
                                     config.settings["window_width"] -
                                     2 * self.very_wide_padding.x,
                                     padding=self.wider_padding,
                                     outline_size=self.standard_outline_size,
                                     empty_text="Item text",
                                     outline_colour=(150, 150, 150),
                                     empty_text_colour=(130, 130, 130))
        self.item_text_entry.position = self.large_padding.copy()
        self.item_text_entry.position.y = category_buttons.position.y + category_buttons.height + self.large_padding.y
        self.item_desc_entry = Entry(self.medium_large_ui_font,
                                     config.settings["window_width"] -
                                     2 * self.very_wide_padding.x,
                                     padding=self.wider_padding,
                                     outline_size=self.standard_outline_size,
                                     empty_text="Item description",
                                     outline_colour=(150, 150, 150),
                                     empty_text_colour=(130, 130, 130))
        self.item_desc_entry.position = self.large_padding.copy()
        self.item_desc_entry.position.y = self.item_text_entry.position.y + self.item_text_entry.height + self.large_padding.y
        self.category_button_size -= 2 * self.standard_outline_size
        start_pos = self.item_desc_entry.position.y + self.item_desc_entry.height
        button_size = Vector2D(
            config.settings["window_width"] // 3 - self.large_padding.x * 2,
            b.height - 2 * self.standard_outline_size.y)
        y_padding = config.settings["window_height"] - start_pos - 4 * (
            button_size.y + 2 * self.standard_outline_size.y)
        y_padding /= 5

        select_item_tags_button = Button(
            "Select tags",
            self.larger_ui_font,
            target=self.LoadThirdTagsBar,
            arguments=[
                {
                    "TYPE": "HIDE",
                    "ID": ComponentID.ITEM_FIRST_BAR.value  # TODO update
                },
                {
                    "TYPE": "JOIN",
                    "ID": ComponentID.TAG_LIST.value,
                },
                {
                    "TYPE": "MOVE",
                    "ID": ComponentID.TAG_LIST.value,
                    "POSITION": Vector2D(0,
                                         config.settings["window_height"] // 7)
                },
                {
                    "TYPE": "DEACTIVATE",
                    "ID": ComponentID.TAG_LIST.value,
                    "CACHE": False
                },
                {
                    "TYPE":
                    "TRANSITION",
                    "TRANSITIONS": [{
                        "ELEMENTS": [
                            ComponentID.ITEM_ADD.value,
                            ComponentID.ITEM_ADD_TAGS.value
                        ],
                        "STYLE":
                        2,
                        "TIME":
                        1,
                        "DELAY":
                        0,
                        "TYPE":
                        "LEAVING"
                    }, {
                        "ELEMENTS": ComponentID.TAG_THIRD_BAR.value,
                        "STYLE": 7,
                        "TIME": 0.5,
                        "DELAY": 0.9,
                        "TYPE": "JOINING"
                    }]
                }
            ],
            padding=MakeElementEqualSize("Select tags", self.larger_ui_font,
                                         button_size),
            outline_size=self.standard_outline_size,
            background_colour=(100, 100, 100),
            pressed_background_colour=(100, 100, 100),
            outline_colour=(150, 150, 150),
            text_colour=(255, 255, 255))
        select_item_tags_button.position = self.large_padding.copy()
        select_item_tags_button.position.y = start_pos + y_padding
        columns = self.tags_container.columns
        rows = self.tags_container.rows
        self.tag_button_movement_arguments = []
        for i in range(rows):
            self.tag_button_movement_arguments.append({
                "ELEMENTS":
                self.tags_buttons[::-1][i * columns:(i + 1) * columns],
                "STYLE":
                21,
                "TIME":
                1,
                "DELAY":
                i * 0.05,
                "TYPE":
                "MOVING"
            })
        self.tag_button_movement_arguments[-1]["POST_ARGS"] = [{
            "TYPE":
            "ACTIVATE",
            "ID":
            ComponentID.TAG_LIST.value
        }]
        select_item_tags_button.arguments[4][
            "TRANSITIONS"] += self.tag_button_movement_arguments

        clear_item_tags_button = Button(
            "Clear tags",
            self.larger_ui_font,
            target=self.ClearItemTags,
            padding=MakeElementEqualSize("Clear tags", self.larger_ui_font,
                                         button_size),
            outline_size=self.standard_outline_size,
            background_colour=(100, 100, 100),
            pressed_background_colour=(100, 100, 100),
            outline_colour=(150, 150, 150),
            text_colour=(255, 255, 255))
        clear_item_tags_button.position = self.large_padding.copy()
        clear_item_tags_button.position.y = select_item_tags_button.position.y + select_item_tags_button.height + y_padding
        import_item_tags_button = Button(
            "Import tags",
            self.larger_ui_font,
            target=self.ImportItemTags,
            padding=MakeElementEqualSize("Import tags", self.larger_ui_font,
                                         button_size),
            outline_size=self.standard_outline_size,
            background_colour=(100, 100, 100),
            pressed_background_colour=(100, 100, 100),
            outline_colour=(150, 150, 150),
            text_colour=(255, 255, 255))
        import_item_tags_button.position = self.large_padding.copy()
        import_item_tags_button.position.y = clear_item_tags_button.position.y + clear_item_tags_button.height + y_padding
        self.import_ignore_list = []
        entry_padding = self.standard_padding
        entry_padding.y = (button_size.y -
                           self.larger_ui_font.size("ABCDEFGH")[1]) / 2
        self.manual_item_tag_search = FunctionalEntry(
            self.larger_ui_font,
            button_size.x + 2 * self.standard_outline_size.x,
            target=self.AttemptAddItemTag,
            padding=entry_padding,
            outline_size=self.standard_outline_size,
            empty_text="Enter tags manually",
            outline_colour=(150, 150, 150),
            empty_text_colour=(130, 130, 130))
        self.manual_item_tag_search.position = self.large_padding.copy()
        self.manual_item_tag_search.position.y = import_item_tags_button.position.y + import_item_tags_button.height + y_padding

        self.item_add_component.AddUIElements(
            self.item_change_back_button, add_item_button,
            self.item_rating_bar, category_buttons, self.item_text_entry,
            self.item_desc_entry, select_item_tags_button,
            clear_item_tags_button, import_item_tags_button,
            self.manual_item_tag_search)
        self.item_add_component.tab_list = [
            self.item_text_entry, self.item_desc_entry,
            self.manual_item_tag_search
        ]

        rect_position = select_item_tags_button.position.copy()
        rect_position.x += select_item_tags_button.width + 2 * self.large_padding.x
        position = rect_position + self.standard_padding
        rect_size = Vector2D(
            config.settings["window_width"] * 2 // 3 -
            2 * self.large_padding.x,
            (config.settings["window_height"] - start_pos) - 2 * y_padding)
        size = rect_size - 2 * self.standard_padding
        self.item_tags_component = ScrollComponent(position,
                                                   size,
                                                   size.y, (75, 75, 75),
                                                   automate_max_scroll=True)
        self.item_tags_component.additional_height = self.standard_padding.y
        self.item_tags_component.UpdateMaxHeight()
        outline_rectangle = Rectangle(rect_size, (150, 150, 150))
        outline_rectangle.position = rect_position
        self.item_add_component.AddUIElement(outline_rectangle)
        self.item_tag_button_width = size.x - (
            config.settings["item_tags_shown_per_row"] +
            1) * self.standard_padding.x
        self.item_tag_button_width /= config.settings[
            "item_tags_shown_per_row"]
        self.item_tag_max_size = self.item_tag_button_width - 2 * (
            self.standard_padding.x + self.standard_outline_size.x)
        self.item_tags_buttons = []

        self.item_fade_arguments = [{
            "TYPE": "JOIN",
            "ID": ComponentID.ITEM_ADD_FADE_LAYER.value
        }, {
            "TYPE":
            "TRANSITION",
            "TRANSITIONS": [{
                "ELEMENTS": (self.ChangeFade, 0),
                "STYLE":
                5,
                "TIME":
                0.5,
                "DELAY":
                0,
                "TYPE":
                "JOINING",
                "POST_ARGS": [{
                    "TYPE": "DEACTIVATE",
                    "ID": ComponentID.ITEM_ADD_FADE_LAYER.value,
                    "CACHE": True
                }]
            }]
        }, {
            "TYPE": "EXECUTE",
            "FUNCTION": self.ChangeFade,
            "ARGUMENTS": [0],
            "KWARGUMENTS": {}
        }]
        self.item_fade_exit_arguments = [{
            "TYPE":
            "ACTIVATE",
            "ID":
            ComponentID.ITEM_ADD_FADE_LAYER.value,
        }, {
            "TYPE":
            "TRANSITION",
            "TRANSITIONS": [{
                "ELEMENTS": (self.ChangeFade, 224),
                "STYLE":
                8,
                "TIME":
                0.5,
                "DELAY":
                0,
                "TYPE":
                "LEAVING",
                "POST_ARGS": [{
                    "TYPE": "LEAVE",
                    "ID": ComponentID.ITEM_ADD_FADE_LAYER.value,
                }]
            }]
        }, {
            "TYPE": "EXECUTE",
            "FUNCTION": self.ChangeFade,
            "ARGUMENTS": [224],
            "KWARGUMENTS": {}
        }]
        self.notification_exit_location = []
        self.notification_skip_all_button = Button(
            "Skip all (11)",
            self.larger_ui_font,
            target=self.SkipAllTagNotifications,
            background_colour=(100, 100, 100),
            pressed_background_colour=(100, 100, 100),
            outline_colour=(150, 150, 150),
            text_colour=(255, 255, 255))
        self.notification_skip_one_button = Button(
            "Skip",
            self.larger_ui_font,
            target=self.SkipOneTagNotification,
            background_colour=(100, 100, 100),
            pressed_background_colour=(100, 100, 100),
            outline_colour=(150, 150, 150),
            text_colour=(255, 255, 255))
        self.notification_add_as_new_button = Button(
            "Add as new tag",
            self.larger_ui_font,
            target=self.AddUnknownAsTag,
            background_colour=(100, 100, 100),
            pressed_background_colour=(100, 100, 100),
            outline_colour=(150, 150, 150),
            text_colour=(255, 255, 255))
        self.notification_add_as_synonym_button = Button(
            "Add as synonym",
            self.larger_ui_font,
            target=self.AddUnknownAsSynonym,
            background_colour=(100, 100, 100),
            pressed_background_colour=(100, 100, 100),
            outline_colour=(150, 150, 150),
            text_colour=(255, 255, 255))

        self.notification_skip_all_button.position.y = self.error_back_button.position.y
        self.notification_skip_one_button.position.y = self.error_back_button.position.y
        self.notification_add_as_new_button.position.y = self.error_back_button.position.y
        self.notification_add_as_synonym_button.position.y = self.error_back_button.position.y

        item_fade_layer = StaticComponent(Vector2D(0, 0),
                                          config.settings["window_size"],
                                          (0, 0, 0, 0))
        item_fade_layer.AddUIElement(self.fade_rectangle)

        window.AddComponent(self.item_add_component,
                            ComponentID.ITEM_ADD.value, False, False)
        window.AddComponent(self.item_tags_component,
                            ComponentID.ITEM_ADD_TAGS.value, False, False)
        window.AddComponent(item_fade_layer,
                            ComponentID.ITEM_ADD_FADE_LAYER.value, False,
                            False)

        window.AddComponent(self.tag_addition_component,
                            ComponentID.ITEM_ADD_TAGS_ADD.value, False, False)
        window.AddComponent(self.tag_change_exit_component,
                            ComponentID.ITEM_ADD_TAGS_ADD_EXIT.value, False,
                            False)
        window.AddComponent(self.synonym_suggestion_component,
                            ComponentID.ITEM_ADD_TAGS_ADD_SUGGESTIONS.value,
                            False, False)
        window.AddComponent(self.selected_synonyms_component,
                            ComponentID.ITEM_ADD_TAGS_ADD_SYNONYMS.value,
                            False, False)

    def UpdateItemTagPositioning(self):
        columns = config.settings["item_tags_shown_per_row"]
        position = self.standard_padding.copy()
        for i, b in enumerate(self.item_tags_buttons):
            b.position = position.copy()
            if (i % columns == (columns - 1)) or (columns == 1):
                position.x = self.standard_padding.x
                position.y += b.height + self.standard_padding.y
            elif columns != 1:
                position.x += b.width + self.standard_padding.x
        self.item_tags_component.UpdateMaxHeight()

    def AddItemTag(self, tag, text=''):
        debug.Log("Added a tag to the item.")
        button_tags = [button.arguments for button in self.item_tags_buttons]
        tag = tag.lower().strip()
        if tag in button_tags:
            return
        if len(text) == 0:  # i.e. text not known i.e. we need to make it:
            text = self.GetDisplayText(tag, self.standard_ui_font,
                                       self.item_tag_max_size)
        tooltip = Label(tag,
                        self.standard_ui_font,
                        padding=self.standard_padding,
                        outline_size=self.standard_outline_size,
                        background_colour=(150, 150, 150),
                        outline_colour=(0, 0, 0)).image
        padding = Vector2D(
            MakeElementEqualSize(text, self.standard_ui_font,
                                 Vector2D(self.item_tag_button_width, 0)).x,
            self.standard_padding.y)
        b = HoverButton(text,
                        self.standard_ui_font,
                        target=self.RemoveItemTag,
                        arguments=text,
                        padding=padding,
                        outline_size=Vector2D(0, 0),
                        background_colour=(75, 75, 75),
                        text_colour=(200, 200, 200),
                        hover_background_colour=(100, 100, 100),
                        tooltip_info=[tooltip, 0.5])
        self.item_tags_buttons.append(b)
        self.item_tags_component.AddUIElement(b)
        self.UpdateItemTagPositioning()
        self.item_tags_component.current_scroll = self.item_tags_component.max_scroll

    def RemoveItemTag(self, tag):
        debug.Log("Removed a tag from the new item.")
        if tag in self.selected_tags:
            self.selected_tags.remove(tag)
        for button in self.item_tags_buttons:
            if button.arguments == tag:
                self.item_tags_buttons.remove(button)
                self.item_tags_component.RemoveUIElement(button)
                break
        self.UpdateItemTagPositioning()

    def ClearItemTags(self):
        self.selected_tags = []
        self.item_tags_buttons = []
        self.item_tags_component.ClearUIElements()

    def DisplayError(self,
                     error,
                     active_component,
                     active_ids,
                     title="ERROR",
                     alternate_buttons=None):
        debug.Log("Displayed an error.")
        prev_height = self.error_label.height
        if title != self.error_title_label.text:
            self.error_title_label.text = title
            self.error_title_label.UpdateImage()
            self.error_title_label.position = Vector2D(
                (self.error_component.size.x - self.error_title_label.width) /
                2, self.standard_outline_size.y + self.standard_padding.y * 3)
        self.error_label.text = error
        if alternate_buttons != None:
            self.error_component.RemoveUIElement(self.error_back_button)
            self.error_component.AddUIElements(*alternate_buttons)
        new_height = (len(self.error_label.display_text) -
                      1) * self.error_label.line_seperation
        for line in self.error_label.display_text:
            new_height += self.error_label.font.size(line)[1]
        new_height += 2 * (self.error_label.padding.y +
                           self.error_label.outline_size.y)
        self.error_label.size = Vector2D(self.error_label.width, new_height)
        self.error_label.height = new_height
        self.error_label.max_height = new_height
        self.error_label.max_scroll = 0
        self.error_label.UpdateImage()
        height_change = new_height - prev_height
        self.error_component.size.y += height_change
        self.error_component.height += height_change
        self.error_component.UpdateImage()
        self.error_background_rect.size.y += height_change
        self.error_background_rect.height += height_change
        self.error_background_rect.UpdateImage()
        button_y = self.error_label.position.y + self.error_label.height + self.standard_padding.y
        if alternate_buttons != None:
            for button in alternate_buttons:  # only change y, not x.
                button.position.y = button_y
        else:
            self.error_back_button.position.y = button_y
        self.error_component.position = ScalePosition(
            Vector2D(0, 0), config.settings["window_size"], Vector2D(0.5, 0.5),
            self.error_component.size)
        self.error_component.position.y -= config.settings["window_height"]
        deactivations = []
        post_commands = []
        for id_ in active_ids:
            deactivations.append({
                "TYPE": "DEACTIVATE",
                "ID": id_,
                "CACHE": True
            })
            post_commands.append({"TYPE": "ACTIVATE", "ID": id_})
        if alternate_buttons != None:
            for button in alternate_buttons:
                post_commands.append({
                    "TYPE": "EXECUTE",
                    "FUNCTION": self.error_component.RemoveUIElement,
                    "ARGUMENTS": [button],
                    "KWARGUMENTS": {}
                })
            post_commands.append({
                "TYPE": "EXECUTE",
                "FUNCTION": self.error_component.AddUIElement,
                "ARGUMENTS": [self.error_back_button],
                "KWARGUMENTS": {}
            })
        active_component.AddCommands(
            {
                "TYPE": "JOIN",
                "ID": ComponentID.ERROR.value
            }, {
                "TYPE":
                "TRANSITION",
                "TRANSITIONS": [{
                    "ELEMENTS": ComponentID.ERROR.value,
                    "STYLE": 15,
                    "TIME": 0.75,
                    "DELAY": 0,
                    "TYPE": "MOVING"
                }]
            }, *deactivations)
        for command in post_commands:
            self.error_exit_argument["TRANSITIONS"][0]["POST_ARGS"].append(
                command)
        self.error_exit_argument["TRANSITIONS"][0]["POST_ARGS"].append({
            "TYPE":
            "EXECUTE",
            "FUNCTION":
            self.ResetErrorExitArguments,
            "ARGUMENTS": [],
            "KWARGUMENTS": {}
        })

    def ResetErrorExitArguments(self):
        self.error_exit_argument["TRANSITIONS"][0]["POST_ARGS"].clear()

    def CreateErrorMenu(self, window):  #8
        component_size = Vector2D(config.settings["window_width"] * 2 // 3, 0)
        self.error_title_label = Label("ERROR",
                                       self.smaller_title_ui_font,
                                       padding=self.standard_padding,
                                       text_colour=(200, 200, 200),
                                       outline_size=Vector2D(0, 0))
        self.error_title_label.position = Vector2D(
            (component_size.x - self.error_title_label.width) / 2,
            self.standard_outline_size.y + self.standard_padding.y * 3)
        component_size.y += self.error_title_label.height + self.standard_padding.y
        error_label_size = Vector2D(
            config.settings["window_width"] * 0.6,
            self.larger_ui_font.size('ABCDEFG')[1] +
            2 * self.standard_padding.y)
        self.error_label = AdvancedLabel('',
                                         self.larger_ui_font,
                                         error_label_size,
                                         padding=self.standard_padding,
                                         outline_colour=(0, 0, 0, 0),
                                         text_colour=(200, 200, 200),
                                         outline_size=Vector2D(0, 0))
        self.error_label.position = Vector2D(
            (component_size.x - self.error_label.width) / 2, component_size.y)
        component_size.y += self.error_label.height + self.standard_padding.y
        self.error_exit_argument = {
            "TYPE":
            "TRANSITION",
            "TRANSITIONS": [{
                "ELEMENTS": ComponentID.ERROR.value,
                "STYLE": 14,
                "TIME": 0.75,
                "DELAY": 0,
                "TYPE": "LEAVING",
                "POST_ARGS": []
            }]
        }
        self.error_back_button = Button(
            "OK",
            self.large_ui_font,
            None,
            arguments=self.error_exit_argument,
            padding=self.wider_padding,
            outline_size=self.standard_outline_size,
            background_colour=(37, 123, 200),
            pressed_background_colour=(37, 123, 200),
            outline_colour=(255, 255, 255),
            text_colour=(255, 255, 255))
        self.error_back_button.position = Vector2D(
            component_size.x - self.wider_padding.x -
            self.error_back_button.width, component_size.y)
        component_size.y += self.error_back_button.height + self.standard_padding.y * 3
        position = ScalePosition(Vector2D(0, 0),
                                 config.settings["window_size"],
                                 Vector2D(0.5, 0.5), component_size)
        self.error_component = StaticComponent(position, component_size,
                                               (150, 150, 150))
        self.error_back_button.target = self.error_component.AddCommands
        rect_size = component_size - 2 * self.standard_outline_size
        self.error_background_rect = Rectangle(rect_size, (50, 50, 50))
        self.error_background_rect.position = self.standard_outline_size
        self.error_component.AddUIElements(self.error_background_rect,
                                           self.error_title_label,
                                           self.error_label,
                                           self.error_back_button)

        size = Vector2D(config.settings["window_width"],
                        2 * config.settings["window_height"])
        error_fade_layer = StaticComponent(Vector2D(0, 0), size, (0, 0, 0, 0))
        error_fade_layer.AddUIElement(self.fade_rectangle)

        window.AddComponent(self.error_component, ComponentID.ERROR.value,
                            False, False)
        window.AddComponent(error_fade_layer,
                            ComponentID.ERROR_FADE_LAYER.value, False, False)

    def AddNotification(self,
                        message,
                        display_time=5,
                        delay=0,
                        alternate_tooltip=None):
        text = message if len(message) <= 50 else (message[:50] + "...")
        if alternate_tooltip == None:
            tooltip_text = message
        else:
            tooltip_text = alternate_tooltip
        tooltip = Label(tooltip_text,
                        self.standard_ui_font,
                        padding=self.standard_padding,
                        outline_size=self.standard_outline_size,
                        background_colour=(150, 150, 150),
                        outline_colour=(0, 0, 0)).image
        position = Vector2D(self.standard_padding.x,
                            config.settings["window_height"])
        notification_label = Label(text,
                                   self.standard_ui_font,
                                   self.standard_padding,
                                   self.standard_outline_size, (200, 200, 200),
                                   (0, 0, 0),
                                   tooltip_info=[tooltip, 0],
                                   position=position)
        # not sure if unecessarily inefficient but want to avoid pointer issues
        elements = [e for e in self.notification_component.ui_elements
                    ] + [notification_label]
        movement_vector = Vector2D(
            -notification_label.width - self.standard_padding.x, 0)
        self.notification_component.AddUIElement(notification_label)
        self.notification_component.AddCommands({
            "TYPE":
            "TRANSITION",
            "TRANSITIONS": [
                {
                    "ELEMENTS": elements,
                    "STYLE": 16,
                    "TIME": 1,
                    "DELAY": delay,
                    "TYPE": "MOVING"
                },
                {
                    "ELEMENTS": notification_label,
                    "STYLE": 17,
                    "TIME": display_time,
                    "DELAY": 1 + delay,
                    "TYPE": "MOVING"
                },
                {
                    "ELEMENTS":
                    notification_label,
                    "STYLE":
                    18,
                    "TIME":
                    1,
                    "DELAY":
                    1 + delay + display_time,
                    "TYPE":
                    "MOVING",
                    "MOVEMENT_VECTOR":
                    movement_vector,
                    "POST_ARGS": [{
                        "TYPE": "EXECUTE",
                        "FUNCTION":
                        self.notification_component.RemoveUIElement,
                        "ARGUMENTS": [notification_label],
                        "KWARGUMENTS": {}
                    }]
                },
            ]
        })

    def CreateNotificationMenu(
            self, window):  # 9  - always make this the top component TODO
        self.notification_component = StaticComponent(
            Vector2D(0, 0), config.settings["window_size"], (0, 0, 0, 0))

        window.AddComponent(self.notification_component,
                            ComponentID.NOTIFICATION.value, True,
                            True)  # TODO CHANGE (TEMP)

    def LoadSearchSuggestion(self, suggestion, search_text, cursor_index):
        search_text = search_text.strip().split(" ")
        selected_word = None
        word_index = 0
        for i, word in enumerate(search_text):
            cursor_index -= len(word)
            if cursor_index <= 0:
                selected_word = word
                cursor_index += len(word)
                word_index = i
                break
            cursor_index -= 1
        if (selected_word == None) or (len(selected_word) == 0) or (
                selected_word
                in self.disallowed_characters) or (selected_word
                                                   in self.disallowed_phrases):
            return None

        replaced = False
        selected = ''
        for i, char in enumerate(selected_word):
            if char == "(" or char == ")":
                selected += char
            elif char == "[":
                selected += selected_word[i:]
                break
            elif not replaced:
                if char in Operators.pre_operators:
                    selected += char
                else:
                    selected += "~"
                    replaced = True
        selected = selected.replace("~", suggestion)
        search_text[word_index] = selected
        self.search_bar.text = " ".join(search_text)
        self.search_bar.cursor_index -= len(selected_word)
        self.search_bar.cursor_index += len(selected)
        self.search_bar.UpdateText()

    def GetSearchSuggestions(self, search_text, cursor_index, max_suggestions):
        search_text = search_text.strip().lower().split(" ")
        selected_word = None
        for word in search_text:
            cursor_index -= len(word)
            if cursor_index <= 0:
                selected_word = word
                cursor_index += len(word)
                break
            cursor_index -= 1
        if (selected_word == None) or (len(selected_word) == 0) or (
                selected_word
                in self.disallowed_characters) or (selected_word
                                                   in self.disallowed_phrases):
            return None
        selected_word = selected_word.replace("(", "")
        selected_word = selected_word.replace(")", "")
        for i, char in enumerate(selected_word):
            if char == "[" or char == "]":
                selected_word = selected_word[:i]
                break
        if selected_word[0] in Operators.pre_operators:
            selected_word = selected_word[1:]
        suggestions = []
        formatted = selected_word[:cursor_index] + "*" + selected_word[
            cursor_index:]
        if not formatted[0] == "*":
            formatted = "*" + formatted
        if not formatted[-1] == "*":
            formatted += "*"
        num = 0
        for tag_info in self.tag_cache:
            if tag_info[0] == selected_word:
                suggestions.append(tag_info[0])
                num += 1
                if num == max_suggestions:
                    break
                continue
            names = [tag_info[0]] + tag_info[2]  # name + synonyms
            filtered = WildcardMatch(names, formatted)
            if len(filtered) > 0:
                suggestions.append(tag_info[0])
                num += 1
                if num == max_suggestions:
                    break
        return suggestions

    def MakeEqualWidth(self, elements):
        max_width = max(*[e.width for e in elements])
        for e in elements:
            if e.width != max_width:
                e.padding = e.padding.copy()
                e.padding.x += (max_width - e.width) / 2
                e.UpdateImage()

    def SelectSearchFormat(self, pressed, index):
        buttons = [
            self.format_text_button, self.format_report_button,
            self.format_html_button
        ]
        if pressed:
            for i, b in enumerate(buttons):
                if i != index:
                    b.pressed = False
        else:
            buttons[index].pressed = True  # can't have nothing pressed
        self.format_help_tt.text = "\n".join(
            self.format_help_tt.text.split("\n")[:-1]
        ) + f"\nYou currently have the '{buttons[index].text}' format selected."

    def SelectSearchType(self, pressed, index):
        buttons = [
            self.type_strict_button, self.type_weighted_button,
            self.type_extreme_button
        ]
        if pressed:
            for i, b in enumerate(buttons):
                if i != index:
                    b.pressed = False
        else:
            buttons[index].pressed = True  # can't have nothing pressed
        self.minimum_score_container.active = self.type_weighted_button.pressed
        self.minimum_score_container.hidden = not self.type_weighted_button.pressed
        if self.type_weighted_button.pressed:
            self.search_component.tab_list = [
                self.search_bar, self.minimum_score_entry
            ]
        else:
            self.search_component.tab_list = [self.search_bar]
            if self.search_component.current_tab_index == 1:
                self.search_component.current_tab_index = 0
        self.type_help_tt.text = "\n".join(
            self.type_help_tt.text.split("\n")[:-1]
        ) + f"\nYou currently have the '{buttons[index].text}' search type selected."

    def GetMinimumWeightedScore(self):
        text = self.minimum_score_entry.text
        if len(text) == 0:
            self.AddNotification("You must enter a minimum score")
            return None
        try:
            score = int(text)
            return score
        except:
            self.AddNotification("The entered minimum score is invalid")
            return None

    def LoadSearchOutput(self, output):
        # TODO temp change when functionality implemented
        if len(output) == 0:
            self.AddNotification("No matching items were found")
            return
        text = ""
        if self.format_text_button.pressed:
            self.search_output_label.scroll_speed = config.settings[
                "scroll_speed"] * 25
            if self.type_weighted_button.pressed:
                temp_out = output.keys()
                output = sorted(list(temp_out),
                                key=lambda k: output[k],
                                reverse=True)
            for match in output:
                text += f'{SQL.GetItemTextFromID(match)}\n'
        elif self.format_report_button.pressed:
            self.search_output_label.scroll_speed = config.settings[
                "scroll_speed"] * 25
            pass
        elif self.format_html_button.pressed:
            self.search_output_label.scroll_speed = config.settings[
                "scroll_speed"] * 60
            items = [SQL.GetItemTextFromID(i) for i in output]
            text += FormatResultsToHTML(items)
        else:
            return
        self.search_output_label.text = text
        self.search_component.AddCommands({
            "TYPE":
            "TRANSITION",
            "TRANSITIONS": [{
                "ELEMENTS": ComponentID.SEARCH.value,
                "STYLE": 2,
                "TIME": 1,
                "DELAY": 0,
                "TYPE": "LEAVING"
            }, {
                "ELEMENTS": ComponentID.SEARCH_RESULT.value,
                "STYLE": 2,
                "TIME": 1,
                "DELAY": 0,
                "TYPE": "JOINING"
            }]
        })

    def MakeSearch(self, search_text):
        if len(search_text) == 0 or len(search_text.replace(" ", "")) == 0:
            return
        try:
            search_text = search_text.strip()
            if self.search_bar.is_focused:
                self.search_bar.is_focused = False
                self.search_bar.Unfocus()
            if self.type_strict_button.pressed:
                matches = StrictSearch(search_text)
                if isinstance(matches, tuple) and matches[0] == "INVALID":
                    if matches[1] == "TAGS":
                        self.AddNotification(
                            "Search contains tags that do not exist")
                    elif matches[1] == "VALIDITY":
                        self.AddNotification(
                            "Innapropriate query for a strict search.")
                    return
                self.LoadSearchOutput(matches)
            elif self.type_weighted_button.pressed:
                min_score = self.GetMinimumWeightedScore()
                if min_score == None:
                    return
                matches = WeightedSearch(search_text, minimum_score=min_score)
                if isinstance(matches, tuple) and matches[0] == "INVALID":
                    if matches[1] == "TAGS":
                        self.AddNotification(
                            "Search contains tags that do not exist")
                    elif matches[1] == "VALIDITY":
                        self.AddNotification(
                            "Innapropriate query for a weighted search.")
                    return
                self.LoadSearchOutput(matches)
            elif self.type_extreme_button.pressed:
                matches = ExtremeSearch(search_text)
                if isinstance(matches, tuple) and matches[0] == "INVALID":
                    if matches[1] == "TAGS":
                        self.AddNotification(
                            "Search contains tags that do not exist")
                    elif matches[1] == "VALIDITY":
                        self.AddNotification(
                            "Innapropriate query for an extreme search.")
                    return
                self.LoadSearchOutput(matches)
        except:
            self.AddNotification("Invalid search query")

    def MakeSearchFromButton(self):
        self.MakeSearch(self.search_bar.text)

    def CreateAdvancedTooltip(self, text, font, padding, outline_size,
                              line_seperation, *args, **kwargs):
        max_width = 0
        height = 2 * (self.standard_outline_size.y +
                      self.standard_padding.y) - line_seperation
        for line in text.split("\n"):
            size = Vector2D(self.standard_ui_font.size(line))
            if size.x > max_width:
                max_width = size.x
            height += size.y + line_seperation
        size = Vector2D(max_width + 2 * (padding.x + outline_size.x), height)
        return AdvancedLabel(text, font, size, padding, outline_size, *args,
                             **kwargs)

    def ResetSearchesMenu(self):
        self.tag_cache = SQL.GetAllTagData()
        self.search_bar.Reset()
        self.minimum_score_entry.Reset()
        self.format_text_button.pressed = True
        self.format_help_tt.text = "\n".join(
            self.format_help_tt.text.split("\n")[:-1]
        ) + "\nYou currently have the 'Text only' format selected by default."
        self.format_report_button.pressed = False
        self.format_html_button.pressed = False
        self.type_strict_button.pressed = True
        self.type_help_tt.text = "\n".join(
            self.type_help_tt.text.split("\n")[:-1]
        ) + "\nYou currently have the 'Strict' search type selected by default."
        self.type_weighted_button.pressed = False
        self.type_extreme_button.pressed = False
        self.minimum_score_container.active = False
        self.minimum_score_container.hidden = True
        self.search_component.tab_list = [self.search_bar]
        self.search_component.current_tab_index = None

    def CreateSearchesMenu(self, window):
        self.search_component = StaticComponent(Vector2D(0, 0),
                                                config.settings["window_size"],
                                                (0, 0, 0, 0))
        self.tag_cache = []
        bar_size = Vector2D(config.settings["window_width"],
                            config.settings["window_height"] // 7)
        bar_background = Rectangle(bar_size, (50, 50, 50), is_active=False)
        back_button = Button("Back",
                             self.larger_ui_font,
                             target=self.search_component.AddCommands,
                             arguments={
                                 "TYPE":
                                 "TRANSITION",
                                 "TRANSITIONS": [{
                                     "ELEMENTS":
                                     ComponentID.SEARCH.value,
                                     "STYLE":
                                     24,
                                     "TIME":
                                     1,
                                     "DELAY":
                                     0,
                                     "TYPE":
                                     "LEAVING"
                                 }, {
                                     "ELEMENTS": ComponentID.MAIN.value,
                                     "STYLE": 24,
                                     "TIME": 1,
                                     "DELAY": 0,
                                     "TYPE": "JOINING"
                                 }]
                             },
                             padding=self.wider_padding,
                             outline_size=self.standard_outline_size,
                             outline_colour=(255, 255, 255),
                             pressed_background_colour=(200, 200, 200))
        back_button.position.x = self.very_wide_padding.x
        back_button.position.y = (bar_size.y - back_button.height) / 2
        tt_text = """In this menu you can search for items based on their tags.

By default, leaving a space between two tags means 'AND' i.e. both must be included.

You can also use the NOT, OR and XOR logical operations, but for strict and weighted
searches these options are only available when in one set of brackets.

Typing a '-' or an '!' before a tag name is equivalent to a NOT operation. For example:
'tag1 -tag2 (tag3 ~ !tag4)' is the same as 'tag1 AND NOT tag2 AND (tag3 OR NOT tag4)'
A plus (+) is implied but simply means inclusion. i.e. 'tag1' is identical to '+tag1'.

&& = & = AND
~ = || = OR 
^ = XOR

You can also use * as a wildcard, for example '*f*' will display items with tags that
contain an 'f' character, or 'red*' will display items with tags that start with
the phrase 'red'."""
        general_help_tt = self.CreateAdvancedTooltip(
            tt_text,
            self.standard_ui_font,
            self.standard_padding,
            self.standard_outline_size,
            self.standard_outline_size.y,
            background_colour=(200, 200, 200),
            outline_colour=(0, 0, 0))
        help_label = Label("?",
                           self.larger_ui_font,
                           padding=self.very_wide_padding,
                           outline_size=self.standard_outline_size,
                           background_colour=(200, 200, 200),
                           outline_colour=(0, 0, 0),
                           tooltip_info=[general_help_tt, 0.05])
        help_label.position.x = config.settings[
            "window_width"] - help_label.width - self.very_wide_padding.x
        help_label.position.y = (bar_size.y - help_label.height) / 2
        search_button = Button("Search",
                               self.larger_ui_font,
                               target=self.MakeSearchFromButton,
                               padding=self.wider_padding,
                               outline_size=self.standard_outline_size,
                               background_colour=(37, 123, 200),
                               pressed_background_colour=(37, 123, 200),
                               outline_colour=(255, 255, 255),
                               text_colour=(255, 255, 255))
        search_button.position.x = help_label.position.x - search_button.width - self.very_wide_padding.x
        search_button.position.y = (bar_size.y - search_button.height) / 2
        search_bar_pos_x = back_button.position.x + back_button.width + self.very_wide_padding.x
        search_bar_width = search_button.position.x - self.very_wide_padding.x - search_bar_pos_x
        self.search_bar = SearchBar(
            self.larger_ui_font,
            search_bar_width,
            self.MakeSearch,
            self.GetSearchSuggestions,
            suggestion_use_function=self.LoadSearchSuggestion,
            max_suggestions=4,
            padding=self.wider_padding,
            outline_size=self.standard_outline_size,
            empty_text="Enter a search here",
            outline_colour=(150, 150, 150),
            empty_text_colour=(130, 130, 130),
            search_background_colour=(150, 150, 150),
            suggestion_background_colour=(200, 200, 200))
        self.search_bar.position.x = search_bar_pos_x
        self.search_bar.position.y = (bar_size.y - self.search_bar.height) / 2

        format_container = Container(5,
                                     1,
                                     inner_padding=self.extremely_wide_padding)
        type_container = Container(5,
                                   1,
                                   inner_padding=self.extremely_wide_padding)
        format_label = Label("Format:", self.large_ui_font)
        type_label = Label("Search type:", self.large_ui_font)
        self.MakeEqualWidth([format_label, type_label])
        self.format_text_button = CheckButton(
            "Text only",
            self.larger_ui_font,
            target=self.SelectSearchFormat,
            arguments=[0],
            padding=self.very_wide_padding,
            outline_size=self.standard_outline_size)
        self.type_strict_button = CheckButton(
            "Strict",
            self.larger_ui_font,
            target=self.SelectSearchType,
            arguments=[0],
            padding=self.very_wide_padding,
            outline_size=self.standard_outline_size)
        self.MakeEqualWidth([self.format_text_button, self.type_strict_button])
        self.format_report_button = CheckButton(
            "Report",
            self.larger_ui_font,
            target=self.SelectSearchFormat,
            arguments=[1],
            padding=self.very_wide_padding,
            outline_size=self.standard_outline_size)
        self.type_weighted_button = CheckButton(
            "Weighted",
            self.larger_ui_font,
            target=self.SelectSearchType,
            arguments=[1],
            padding=self.very_wide_padding,
            outline_size=self.standard_outline_size)
        self.MakeEqualWidth(
            [self.format_report_button, self.type_weighted_button])
        self.format_html_button = CheckButton(
            "HTML",
            self.larger_ui_font,
            target=self.SelectSearchFormat,
            arguments=[2],
            padding=self.very_wide_padding,
            outline_size=self.standard_outline_size)
        self.type_extreme_button = CheckButton(
            "Extreme",
            self.larger_ui_font,
            target=self.SelectSearchType,
            arguments=[2],
            padding=self.very_wide_padding,
            outline_size=self.standard_outline_size)
        self.MakeEqualWidth(
            [self.format_html_button, self.type_extreme_button])
        tt_text = """This option dictates the format of the search output.

'Text only' will simply display the items in their simplest form, listing them out line-by-line.

'Report' will create a report-style format, giving more information about each item.

'HTML' will output the HTML of a webpage that allows you to view the items in a slideshow-
style format. Clicking the 'export' button then will load the webpage rather than copy the
output to your clipboard. For casual users, HTML style is recommended.

You currently have the 'Text only' format selected by default."""
        self.format_help_tt = self.CreateAdvancedTooltip(
            tt_text,
            self.standard_ui_font,
            self.standard_padding,
            self.standard_outline_size,
            self.standard_outline_size.y,
            background_colour=(200, 200, 200),
            outline_colour=(0, 0, 0))
        format_help_label = Label("?",
                                  self.larger_ui_font,
                                  padding=self.very_wide_padding,
                                  outline_size=self.standard_outline_size,
                                  background_colour=(200, 200, 200),
                                  outline_colour=(0, 0, 0),
                                  tooltip_info=[self.format_help_tt, 0.05])
        format_container.AddElements(format_label, self.format_text_button,
                                     self.format_report_button,
                                     self.format_html_button,
                                     format_help_label)
        format_container.position = ScalePosition(Vector2D(0, 0),
                                                  self.search_component.size,
                                                  Vector2D(0.5, 2 / 7),
                                                  format_container.size)
        self.format_text_button.pressed = True
        tt_text = """This option dictates the type of search you are performing.

'Strict' searches are the simplest type. You can use basic logical operations and
can only go one nested layer of brackets deep. This will cover most of your searches.

'Weighted' searches are like strict searches, but you can assign a weight/score to
each tag or expression. Each item will be scored based on these conditions, and then
will be compared to a minimum threshold score you enter. No weight will be taken to
mean a weight of 1 by default.
For example, if you have 'tag1[5] tag2 -tag3[10] (tag4 XOR tag5)[3]' you are saying:
"give 5 points if tag1 is present, 1 point if tag2 is present, 10 points if tag3 is
NOT present, and 3 points if one of tag4 or tag5 (but not both) are present."

'Extreme' searches are used for the rare cases where you need to escape the
limitations of a strict search - for example using multiple nested brackets or OR
operations outside of brackets. For example, 'tag1 ~ tag2' is considered extreme,
and so is 'tag1 -tag2 (tag3 XOR (tag5 -(tag6 XOR (tag7 tag8))))'. As can be seen,
this is likely to be rarely used at best, but provides power to those who need it.

You currently have the 'Strict' search type selected by default."""
        self.type_help_tt = self.CreateAdvancedTooltip(
            tt_text,
            self.standard_ui_font,
            self.standard_padding,
            self.standard_outline_size,
            self.standard_outline_size.y,
            background_colour=(200, 200, 200),
            outline_colour=(0, 0, 0))
        type_help_label = Label("?",
                                self.larger_ui_font,
                                padding=self.very_wide_padding,
                                outline_size=self.standard_outline_size,
                                background_colour=(200, 200, 200),
                                outline_colour=(0, 0, 0),
                                tooltip_info=[self.type_help_tt, 0.05])
        type_container.AddElements(type_label, self.type_strict_button,
                                   self.type_weighted_button,
                                   self.type_extreme_button, type_help_label)
        type_container.position = ScalePosition(Vector2D(0, 0),
                                                self.search_component.size,
                                                Vector2D(0.5, 3.5 / 7),
                                                type_container.size)
        self.type_strict_button.pressed = True
        self.minimum_score_container = Container(
            3, 1, inner_padding=self.extremely_wide_padding)
        minimum_score_label = Label("Minimum score:", self.large_ui_font)
        self.minimum_score_entry = Entry(
            self.larger_ui_font,
            config.settings["window_width"] // 5,
            padding=self.very_wide_padding,
            outline_size=self.standard_outline_size,
            empty_text="Enter score")
        tt_text = """This is where you enter a minimum (threshold) score for a weighted search.
All items that do not meet this score threshold will not be output. For example, if you had the 
query 'tag1[2] tag2[1] tag3[1] tag4[1]' and set the minimum score threshold to be 4, this means
that an item must have tag1 and two of tag2, tag3 and tag4 to be shown.

A more intuitive way to ensure a tag shows up is by using a large weight, e.g.
'tag1[10000] tag2[1] tag3[1] tag4[1]' with a minimum score of 1000.

Please note that '-tag1[500]' means 'give 500 score for not having tag1' as opposed to 'deduct
500 score for having tag1' as this will affect your desired outcome scores. If you wanted
'deduct 500 score for having tag1' you should instead use 'tag1[-500]'."""
        min_score_help_tt = self.CreateAdvancedTooltip(
            tt_text,
            self.standard_ui_font,
            self.standard_padding,
            self.standard_outline_size,
            self.standard_outline_size.y,
            background_colour=(200, 200, 200),
            outline_colour=(0, 0, 0))
        minimum_score_help_label = Label(
            "?",
            self.larger_ui_font,
            padding=self.very_wide_padding,
            outline_size=self.standard_outline_size,
            background_colour=(200, 200, 200),
            outline_colour=(0, 0, 0),
            tooltip_info=[min_score_help_tt, 0.5])
        self.minimum_score_container.AddElements(minimum_score_label,
                                                 self.minimum_score_entry,
                                                 minimum_score_help_label)
        self.minimum_score_container.position = ScalePosition(
            Vector2D(0, 0), self.search_component.size, Vector2D(0.5, 5 / 7),
            self.minimum_score_container.size)
        self.minimum_score_container.active = False
        self.minimum_score_container.hidden = True

        favourites_button = Button("View favourite searches",
                                   self.larger_ui_font,
                                   target=print,
                                   arguments=None,
                                   padding=self.very_wide_padding,
                                   outline_size=self.standard_outline_size,
                                   pressed_background_colour=(200, 200, 200))
        favourites_button.position = ScalePosition(Vector2D(0, 0),
                                                   self.search_component.size,
                                                   Vector2D(0, 6.5 / 7),
                                                   favourites_button.size)
        favourites_button.position.x = self.very_wide_padding.x

        for element in [
                self.type_strict_button, self.type_weighted_button,
                self.type_extreme_button, self.format_html_button,
                self.format_report_button, self.format_text_button,
                self.minimum_score_entry
        ]:
            element.conditions.append(self.search_bar.IsUnfocused)

        self.search_component.AddUIElements(bar_background, back_button,
                                            search_button, help_label,
                                            format_container, type_container,
                                            self.minimum_score_container,
                                            favourites_button, self.search_bar)
        self.search_component.tab_list = [self.search_bar]
        self.search_component.reset_func = self.ResetSearchesMenu

        window.AddComponent(self.search_component, ComponentID.SEARCH.value,
                            False, False)

    def SkipResultRatings(self):
        self.search_result_component.AddCommands({
            "TYPE":
            "TRANSITION",
            "TRANSITIONS": [{
                "ELEMENTS": ComponentID.SEARCH.value,
                "STYLE": 1,
                "TIME": 1,
                "DELAY": 0,
                "TYPE": "JOINING"
            }, {
                "ELEMENTS": ComponentID.SEARCH_RESULT.value,
                "STYLE": 1,
                "TIME": 1,
                "DELAY": 0,
                "TYPE": "LEAVING"
            }]
        })

    def GetResultsExport(self):
        return self.search_output_label.text

    def ExportResultsToClipboard(self):
        from pyperclip import copy as CopyToClipboard
        CopyToClipboard(self.GetResultsExport())
        self.AddNotification("Search results copied to clipboard")

    def LoadHTMLResults(self, p_arg):
        try:
            import subprocess
            from time import sleep as SleepTime
            p = subprocess.Popen(p_arg)
            p.wait()
            self.AddNotification("Opened results in firefox.")
            SleepTime(5)
            with open('resources\\temp_html.html', 'w+') as f:
                f.truncate(0)
                f.close()
        except:
            self.AddNotification("Failed to open results in firefox.")
            self.ExportResultsToClipboard()

    def ExportResultsGeneral(self):
        if self.format_html_button.pressed:
            #try:
            import os.path
            firefox_path = r'C:\Program Files (x86)\Mozilla Firefox\Firefox.exe'
            if not os.path.isfile(firefox_path):
                firefox_path = r'C:\Program Files\Mozilla Firefox\Firefox.exe'
                if not os.path.isfile(firefox_path):
                    self.ExportResultsToClipboard()
                    return
            with open('resources\\temp_html.html', 'w+') as f:
                f.write(self.GetResultsExport())
                f.close()
            self.search_result_component.AddCommand({
                "TYPE":
                "EXECUTE",
                "FUNCTION":
                self.LoadHTMLResults,
                "ARGUMENTS": [[
                    firefox_path, '-private-window',
                    'file://' + os.path.realpath('resources\\temp_html.html')
                ]],
                "KWARGUMENTS":
                None,
                "THREADED":
                True
            })
            #except:
            #    self.ExportResultsToClipboard()
        else:
            self.ExportResultsToClipboard()

    def ExportResultsToFile(self, filename=None):
        try:
            if filename == None:
                if not self.file_dialog_used:
                    self.SetupDefaultFileDialog()
                    self.file_dialog_used = True
                from tkinter.filedialog import asksaveasfile as AskSaveAsFile
                if self.format_html_button.pressed:
                    filetypes = (("Text files", "*.txt"), ("HTML files",
                                                           "*.html"))
                    default = "html"
                else:
                    filetypes = (("Text files", "*.txt"), )
                    default = "txt"
                file_ = AskSaveAsFile(
                    title="Create a file to save the search results to",
                    filetypes=filetypes,
                    defaultextension=default)
            else:
                file_ = open(filename, 'w+')
            if file_ != None:
                debug.Log(f'Exported search results to a file.')
                file_.write(self.GetResultsExport())
                file_.close()
                self.AddNotification(
                    "Search results successfully exported to file")
        except:
            self.AddNotification("An error occurred accessing the file")

    def CreateSearchResultMenu(self, window):
        self.search_result_component = StaticComponent(
            Vector2D(0, 0), config.settings["window_size"], (50, 50, 50))

        label_size = Vector2D(config.settings["window_width"] * 0.8,
                              config.settings["window_height"] * 0.8)
        self.search_output_label = AdvancedLabel(
            '',
            self.larger_ui_font,
            label_size,
            padding=self.wider_padding,
            outline_size=self.standard_outline_size,
            background_colour=(150, 150, 150),
            outline_colour=(255, 255, 255),
            line_seperation=self.search_result_component.height // 400,
            auto_scroll_position=0)
        self.search_output_label.position = ScalePosition(
            Vector2D(0, 0), self.search_result_component.size,
            Vector2D(0.5, 0.425), self.search_output_label.size)

        button_container = Container(4,
                                     1,
                                     inner_padding=self.extremely_wide_padding)
        continue_button = Button("Continue",
                                 self.large_ui_font,
                                 target=print,
                                 padding=self.standard_padding,
                                 outline_size=self.standard_outline_size,
                                 pressed_background_colour=(200, 200, 200),
                                 outline_colour=(255, 255, 255))
        skip_button = Button("Skip rating",
                             self.large_ui_font,
                             target=self.SkipResultRatings,
                             padding=self.standard_padding,
                             outline_size=self.standard_outline_size,
                             pressed_background_colour=(200, 200, 200),
                             outline_colour=(255, 255, 255))
        export_button = Button("Export",
                               self.large_ui_font,
                               target=self.ExportResultsGeneral,
                               padding=self.standard_padding,
                               outline_size=self.standard_outline_size,
                               pressed_background_colour=(200, 200, 200),
                               outline_colour=(255, 255, 255))
        export_to_file_button = Button("Export to file",
                                       self.large_ui_font,
                                       target=self.ExportResultsToFile,
                                       padding=self.standard_padding,
                                       outline_size=self.standard_outline_size,
                                       pressed_background_colour=(200, 200,
                                                                  200),
                                       outline_colour=(255, 255, 255))
        button_container.AddElements(continue_button, skip_button,
                                     export_button, export_to_file_button)
        button_container.position = ScalePosition(
            Vector2D(0, 0), self.search_result_component.size,
            Vector2D(0.5, 0.9), button_container.size)
        self.search_result_component.AddUIElements(self.search_output_label,
                                                   button_container)

        window.AddComponent(self.search_result_component,
                            ComponentID.SEARCH_RESULT.value, False, False)


if __name__ == "__main__":
    #try:
    testLoop = interaction.MainLoop()
    debug.Log(f'Running Version {config.version}')
    constructor = MenuConstructor()
    constructor.ConstructStartMenus(testLoop)
    testLoop.Start()
#except Exception as e:
#    print(e)
#    input()
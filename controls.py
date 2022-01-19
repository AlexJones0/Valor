import pygame


class ControlsObject(dict):
    """ A subclass of a dictionary, used to store the current state of the
        user-input controls."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @property
    def MouseClicked(self):
        """ A property that returns a Boolean value describing whether the mouse
            was clicked (not pressed down, specifically clicked) in the last
            control update or not. No inputs, and it outputs a Boolean value."""
        for event in self["events"]:
            if event.type == pygame.MOUSEBUTTONDOWN:
                return True
        return False

    @property
    def LeftClickDown(self):
        for event in self["events"]:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                return True
        return False

    @property
    def LeftClickRelease(self):
        for event in self["events"]:
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                return True
        return False

    @property
    def MouseHasMoved(self):
        for event in self["events"]:
            if event.type == pygame.MOUSEMOTION:
                return True
        return False

    @property
    def MouseHasScrolled(self):
        for event in self["events"]:
            if event.type == pygame.MOUSEBUTTONDOWN and 4 <= event.button <= 5:
                return True
        return False

    def PrintIndexOfDown(self):
        """a function for dev use only, prints the indexes of keys that are pressed down."""
        keys = []
        for index, key in enumerate(self["keys_pressed"]):
            if key:
                keys.append(index)
        print(keys)

    def PrintNameOfKeyDown(self):
        """a function for dev use only, prints the names of keys that are pressed down."""
        keys = []
        for event in self["events"]:
            if event.type == pygame.KEYDOWN:
                keys.append(pygame.key.name(event.key))
        print(keys)


controls = ControlsObject()
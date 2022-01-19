from controls import controls
from vectors import Vector2D
import pygame
import config
from time import time as CurrentTime
from pyperclip import copy as CopyToClipboard
from pyperclip import paste as PasteFromClipboard


def CoordInBoundingBox(coord, bounding1, bounding2):
    return ((bounding1.x <= coord.x <= bounding2.x) or \
            (bounding2.x <= coord.x <= bounding1.x)) and \
            ((bounding1.y <= coord.y <= bounding2.y) or \
            (bounding2.y <= coord.y <= bounding1.y))


def ScalePosition(lower_pos,
                  upper_pos,
                  positioning,
                  object_size=None,
                  scale_from=Vector2D(0.5, 0.5)):
    new_x = (upper_pos.x - lower_pos.x) * positioning.x + lower_pos.x
    new_y = (upper_pos.y - lower_pos.y) * positioning.y + lower_pos.y
    if object_size is not None:
        new_x -= scale_from.x * object_size.x
        new_y -= scale_from.y * object_size.y
    return Vector2D(new_x, new_y)


class BaseElement:
    def __init__(self,
                 position,
                 is_active,
                 is_hidden,
                 tooltip_image=None,
                 tooltip_hover_time=2,
                 conditions=None):
        self.image = None
        if position is None:
            self.position = Vector2D(0, 0)
        else:  # don't create a copy in case that's not what the user wants.
            self.position = position
        self.active = is_active
        self.hidden = is_hidden

        self.tooltip_image = tooltip_image
        self.started_hovering = 0
        self.tooltip_hover_time = tooltip_hover_time
        self.previously_moved = False
        self.hovering = False

        self.conditions = conditions if conditions != None else []

    def Update(self, shift=Vector2D(0, 0)):
        if not self.active:
            return False
        for condition in self.conditions:
            if not condition():
                return False
        if self.tooltip_image == None:
            return
        mouse_position = Vector2D(controls["mouse_position"]) - shift
        relative = mouse_position - self.position
        if (0 < relative.x < self.width) and (0 < relative.y < self.height):
            if controls.MouseHasMoved or controls.MouseHasScrolled:
                self.previously_moved = True
                self.hovering = False
            else:
                if self.previously_moved:
                    self.started_hovering = CurrentTime()
                elif (CurrentTime() -
                      self.started_hovering) > self.tooltip_hover_time:
                    self.hovering = True
                self.previously_moved = False

    def Draw(self, surface, shift=Vector2D(0, 0), draw_end=None):
        if self.hidden:
            return False
        if self.active and draw_end != None and self.hovering and self.tooltip_image != None:
            position = Vector2D(controls["mouse_position"]) + Vector2D(
                3, 3)  # offset so you can see the whole word
            if isinstance(self.tooltip_image, BaseElement):
                image = pygame.Surface(tuple(self.tooltip_image.size),
                                       pygame.SRCALPHA, 32)
                image.convert_alpha()
                self.tooltip_image.Update(shift=shift)
                self.tooltip_image.Draw(image)
            else:
                image = self.tooltip_image
            tooltip_size = Vector2D(image.get_size())
            if (position.x + tooltip_size.x) > config.settings["window_width"]:
                position.x = config.settings["window_width"] - tooltip_size.x
            if (position.y +
                    tooltip_size.y) > config.settings["window_height"]:
                position.y = config.settings["window_height"] - tooltip_size.y
            draw_end.append((image, tuple(position)))

    def WithinBoundingBox(self, coord1, coord2):
        return CoordInBoundingBox(self.position, coord1, coord2)

    def AddConditions(self, *conditions):
        self.conditions.append(conditions)

    def RemoveCondition(self, condition):
        if condition in self.conditions:
            self.conditions.remove(condition)

    def ClearConditions(self):
        self.conditions = []


class ImageElement(BaseElement):
    def __init__(self,
                 image,
                 position=None,
                 tooltip_info=[None, 2],
                 is_hidden=False):
        super().__init__(position, False, is_hidden, *tooltip_info)
        self.image = image

    def Draw(self, surface, shift=Vector2D(0, 0), draw_end=None):
        if super().Draw(surface, shift, draw_end) == False:
            return False
        surface.blit(self.image, tuple(self.position + shift))


class Rectangle(BaseElement):
    def __init__(self,
                 size,
                 colour,
                 position=None,
                 is_active=True,
                 is_hidden=False):
        super().__init__(position, is_active, is_hidden, None, 2)
        self.size = size
        self.width = self.size.x
        self.height = self.size.y
        self.colour = colour
        self.UpdateImage()

    def UpdateImage(self):
        self.image = pygame.Surface(tuple(self.size), pygame.SRCALPHA, 32)
        self.image.convert_alpha()
        self.image.fill(self.colour)

    def UpdateImageColour(self):
        # a lighter version of UpdateImage that only changes the colour, not the size
        self.image.fill(self.colour)

    def Draw(self, surface, shift=Vector2D(0, 0), draw_end=None):
        if super().Draw(surface, shift, draw_end) == False:
            return False
        surface.blit(self.image, tuple(self.position + shift))


class Label(BaseElement):
    def __init__(self,
                 text,
                 font,
                 padding=Vector2D(0, 0),
                 outline_size=Vector2D(0, 0),
                 background_colour=(255, 255, 255, 0),
                 outline_colour=(0, 0, 0, 0),
                 text_colour=(0, 0, 0),
                 tooltip_info=[None, 2],
                 position=None,
                 is_active=True,
                 is_hidden=False):
        super().__init__(position, is_active, is_hidden, *tooltip_info)
        self.padding = padding
        self.outline_size = outline_size
        self.background_colour = background_colour
        self.outline_colour = outline_colour
        self.text_colour = text_colour
        self.font = font
        self.text = text  # don't call UpdateImage(), text.setter calls that for us.

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, new_text):
        self._text = new_text
        self.UpdateImage()

    def UpdateImage(self):
        image_size = Vector2D(self.font.size(
            self.text)) + 2 * (self.padding + self.outline_size)
        self.size = image_size
        self.width = self.size.x
        self.height = self.size.y
        self.image = pygame.Surface(tuple(self.size), pygame.SRCALPHA, 32)
        self.image.convert_alpha()
        self.image.fill(self.outline_colour)
        smaller_image = pygame.Surface(
            tuple(self.size - 2 * self.outline_size), pygame.SRCALPHA, 32)
        smaller_image.convert_alpha()
        smaller_image.fill(self.background_colour)
        label = self.font.render(self.text, 1, self.text_colour)
        smaller_image.blit(label, tuple(self.padding))
        self.image.blit(smaller_image, tuple(self.outline_size))

    def Draw(self, surface, shift=Vector2D(0, 0), draw_end=None):
        if super().Draw(surface, shift, draw_end) == False:
            return False
        surface.blit(self.image, tuple(self.position + shift))

    def WithinBoundingBox(self, coord1, coord2):
        corners = [
            self.position, self.position + self.size,
            self.position + Vector2D(self.width, 0),
            self.position + Vector2D(0, self.height)
        ]
        for corner in corners:
            if CoordInBoundingBox(corner, coord1, coord2):
                return True
        return CoordInBoundingBox(coord1, corners[0],
                                  corners[1])  # if 1 coord of bounding box
        # is in the label, and it hasn't been detected yet, the bounding box is contained within
        # the label


class AdvancedLabel(BaseElement):
    def __init__(self,
                 text,
                 font,
                 size,
                 padding=Vector2D(0, 0),
                 outline_size=Vector2D(0, 0),
                 background_colour=(255, 255, 255, 0),
                 outline_colour=(0, 0, 0),
                 text_colour=(0, 0, 0),
                 position=None,
                 line_seperation=2,
                 auto_scroll_position=None,
                 tooltip_info=[None, 2],
                 is_active=True,
                 is_hidden=False):
        super().__init__(position, is_active, is_hidden, *tooltip_info)
        self.padding = padding
        self.outline_size = outline_size
        self.background_colour = background_colour
        self.outline_colour = outline_colour
        self.text_colour = text_colour
        self.font = font
        self.size = size
        self.width = self.size.x
        self.height = self.size.y
        self.display_text = ['']
        self.max_height = self.height
        self.max_scroll = 0
        self.current_scroll = 0
        self.scroll_speed = config.settings["scroll_speed"] * 25
        self.line_seperation = line_seperation
        self.auto_scroll_position = auto_scroll_position
        self.text = text  # don't call UpdateImage(), text.setter calls that for us.

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, new_text):
        self._text = new_text
        self.display_text = new_text.split("\n")
        max_line_width = self.width - 2 * (self.padding.x +
                                           self.outline_size.x)
        new_display_text = []
        for i in range(len(self.display_text)):
            new_line = self.display_text[i]
            if new_line == '':  # i.e. an empty line that won't get caught
                new_display_text.append(new_line)
            while new_line != '':
                text = new_line
                new_line = ''
                j = 0
                while self.font.size(text)[0] > max_line_width:
                    new_line = text[-1] + new_line
                    text = text[:-1]
                    j += 1
                new_display_text.append(text)
        self.display_text = new_display_text
        sizes = []
        for line in self.display_text:
            sizes.append(Vector2D(self.font.size(line)))
        height = (len(sizes) - 1) * self.line_seperation
        height += sum([size.y for size in sizes])
        self.max_height = height + 2 * (self.padding.y + self.outline_size.y)
        self.max_scroll = self.max_height - self.height
        if self.auto_scroll_position != None:
            self.current_scroll = self.max_scroll * self.auto_scroll_position
            if self.current_scroll < 0:
                self.current_scroll = 0
        self.UpdateImage()

    def UpdateImage(self):
        self.image = pygame.Surface(tuple(self.size), pygame.SRCALPHA, 32)
        self.image.convert_alpha()
        self.image.fill(self.outline_colour)
        smaller_image = pygame.Surface(
            tuple(self.size - 2 * self.outline_size), pygame.SRCALPHA, 32)
        smaller_image.convert_alpha()
        smaller_image.fill(self.background_colour)
        self.image.blit(smaller_image, tuple(self.outline_size))
        added = Vector2D(0, 0)
        for line in self.display_text:
            position = self.padding + added - Vector2D(0, self.current_scroll)
            if position.y >= self.height:
                label = self.font.render(line, 1, self.text_colour)
                self.image.blit(label, tuple(position))
                break
            elif position.y >= 0:
                label = self.font.render(line, 1, self.text_colour)
                self.image.blit(label, tuple(position))
            else:
                if position.y + self.font.size(line)[1] > 0:
                    label = self.font.render(line, 1, self.text_colour)
                    self.image.blit(label, tuple(position))
            added.y += self.line_seperation + self.font.size(line)[1]

    def Draw(self, surface, shift=Vector2D(0, 0), draw_end=None):
        if super().Draw(surface, shift, draw_end) == False:
            return False
        surface.blit(self.image, tuple(self.position + shift))

    def Update(self, shift=Vector2D(0, 0)):
        if super().Update(shift) == False:
            return False
        for event in controls["events"]:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 5:  #scroll down
                    if self.current_scroll < self.max_scroll:
                        prev_scroll = self.current_scroll
                        self.current_scroll += self.scroll_speed
                        if self.current_scroll > self.max_scroll:
                            self.current_scroll = self.max_scroll
                        if self.current_scroll != prev_scroll:
                            self.UpdateImage()
                elif event.button == 4:  #scroll up
                    if self.current_scroll > 0:
                        prev_scroll = self.current_scroll
                        self.current_scroll -= self.scroll_speed
                        if self.current_scroll < 0:
                            self.current_scroll = 0
                        if self.current_scroll != prev_scroll:
                            self.UpdateImage()

    def WithinBoundingBox(self, coord1, coord2):
        corners = [
            self.position, self.position + self.size,
            self.position + Vector2D(self.width, 0),
            self.position + Vector2D(0, self.height)
        ]
        for corner in corners:
            if CoordInBoundingBox(corner, coord1, coord2):
                return True
        return CoordInBoundingBox(coord1, corners[0],
                                  corners[1])  # if 1 coord of bounding box
        # is in the label, and it hasn't been detected yet, the bounding box is contained within
        # the label


class CheckButton(BaseElement):
    def __init__(self,
                 text,
                 font,
                 target=None,
                 arguments=None,
                 padding=Vector2D(5, 5),
                 outline_size=Vector2D(2, 2),
                 background_colour=(200, 200, 200),
                 pressed_background_colour=(150, 150, 150),
                 outline_colour=(0, 0, 0),
                 text_colour=(0, 0, 0),
                 top_left_padding=None,
                 tooltip_info=[None, 2],
                 position=None,
                 is_active=True,
                 is_hidden=False):
        super().__init__(position, is_active, is_hidden, *tooltip_info)
        self.pressed_image = None
        self.unpressed_image = None
        self.text = text
        self.font = font
        self.target = target
        self.arguments = arguments
        self.padding = padding
        self.top_left_padding = top_left_padding
        self.outline_size = outline_size
        self.background_colour = background_colour
        self.pressed_background_colour = pressed_background_colour
        self.outline_colour = outline_colour
        self.text_colour = text_colour
        self.pressed = False
        self.focused = False
        self.UpdateImage()

    def UpdateImage(self, update_size=True):
        text_size = Vector2D(self.font.size(self.text))
        if update_size:
            self.size = text_size + (self.padding + self.outline_size) * 2
            self.width = self.size.x
            self.height = self.size.y
        larger_image = pygame.Surface(tuple(self.size), pygame.SRCALPHA, 32)
        larger_image.convert_alpha()
        larger_image.fill(self.outline_colour)
        self.pressed_image = larger_image.copy()
        self.pressed_image.convert_alpha()
        self.unpressed_image = larger_image.copy()
        self.unpressed_image.convert_alpha()
        image_size = self.size - self.outline_size * 2
        smaller_pressed_image = pygame.Surface(tuple(image_size),
                                               pygame.SRCALPHA, 32)
        smaller_pressed_image.convert_alpha()
        smaller_pressed_image.fill(self.pressed_background_colour)
        smaller_unpressed_image = pygame.Surface(tuple(image_size),
                                                 pygame.SRCALPHA, 32)
        smaller_unpressed_image.convert_alpha()
        smaller_unpressed_image.fill(self.background_colour)
        text_label = self.font.render(self.text, 1, self.text_colour)
        smaller_pressed_image.blit(
            text_label,
            tuple(self.padding if self.top_left_padding is None else self.
                  top_left_padding))
        smaller_unpressed_image.blit(
            text_label,
            tuple(self.padding if self.top_left_padding is None else self.
                  top_left_padding))
        self.pressed_image.blit(smaller_pressed_image,
                                tuple(self.outline_size))
        self.unpressed_image.blit(smaller_unpressed_image,
                                  tuple(self.outline_size))

    def __CallTarget(self):
        if self.target != None:
            if self.arguments == None:
                self.target(self.pressed)
            elif isinstance(self.arguments, (tuple, list, Vector2D)):
                self.target(self.pressed, *self.arguments)
            else:
                self.target(self.pressed, self.arguments)

    def _Press(self):
        self.pressed = True
        self.__CallTarget()

    def _Unpress(self):
        self.pressed = False
        self.__CallTarget()

    def Draw(self, surface, shift=Vector2D(0, 0), draw_end=None):
        if super().Draw(surface, shift, draw_end) == False:
            return False
        image = self.pressed_image if self.pressed else self.unpressed_image
        surface.blit(image, tuple(self.position + shift))

    def Update(self, shift=Vector2D(0, 0)):
        if super().Update(shift) == False:
            return False
        mouse_position = Vector2D(controls["mouse_position"]) - shift
        relative = mouse_position - self.position
        in_position = 0 < relative.x < self.width and 0 < relative.y < self.height
        if controls.LeftClickDown:
            if in_position:
                self.focused = True
            else:
                self.focused = False
        if controls.LeftClickRelease:
            if in_position and self.focused:
                if self.pressed:
                    self._Unpress()
                else:
                    self._Press()
            self.focused = False

    def WithinBoundingBox(self, coord1, coord2):
        corners = [
            self.position, self.position + self.size,
            self.position + Vector2D(self.width, 0),
            self.position + Vector2D(0, self.height)
        ]
        for corner in corners:
            if CoordInBoundingBox(corner, coord1, coord2):
                return True
        return CoordInBoundingBox(coord1, corners[0],
                                  corners[1])  # if 1 coord of bounding box
        # is in the label, and it hasn't been detected yet, the bounding box is contained within
        # the label


class CacheButton(CheckButton):
    def __init__(self,
                 text,
                 font,
                 target=None,
                 arguments=None,
                 padding=Vector2D(5, 5),
                 outline_size=Vector2D(2, 2),
                 background_colour=(200, 200, 200),
                 pressed_background_colour=(150, 150, 150),
                 outline_colour=(0, 0, 0),
                 text_colour=(0, 0, 0),
                 top_left_padding=None,
                 tooltip_info=[None, 2],
                 position=None,
                 is_active=True,
                 is_hidden=False):
        self.prev_pressed_image = None
        self.prev_unpressed_image = None
        self.use_prev_image = False
        super().__init__(text, font, target, arguments, padding, outline_size,
                         background_colour, pressed_background_colour,
                         outline_colour, text_colour, top_left_padding,
                         tooltip_info, position, is_active, is_hidden)

    def UpdateImage(
            self
    ):  # used so that the image is not misdrawn when run with threads
        self.use_prev_image = True
        self.prev_pressed_image = self.pressed_image
        self.prev_unpressed_image = self.unpressed_image
        super().UpdateImage()
        self.use_prev_image = False

    def Draw(self, surface, shift=Vector2D(0, 0), draw_end=None):
        if BaseElement.Draw(self, surface, shift, draw_end) == False:
            return False
        if self.use_prev_image:
            image = self.prev_pressed_image if self.pressed else self.prev_unpressed_image
        else:
            image = self.pressed_image if self.pressed else self.unpressed_image
        surface.blit(image, tuple(self.position + shift))


class Button(CheckButton):
    def __init__(self,
                 text,
                 font,
                 target=None,
                 arguments=None,
                 padding=Vector2D(5, 5),
                 outline_size=Vector2D(2, 2),
                 background_colour=(200, 200, 200),
                 pressed_background_colour=(150, 150, 150),
                 outline_colour=(0, 0, 0),
                 text_colour=(0, 0, 0),
                 press_time=0,
                 top_left_padding=None,
                 tooltip_info=[None, 2],
                 position=None,
                 is_active=True,
                 is_hidden=False):
        super().__init__(text, font, target, arguments, padding, outline_size,
                         background_colour, pressed_background_colour,
                         outline_colour, text_colour, top_left_padding,
                         tooltip_info, position, is_active, is_hidden)
        self.arguments = arguments
        self.press_time = press_time
        self.time_of_press = 0

    def __CallTarget(self):
        if self.target != None:
            if self.arguments == None:
                self.target()
            elif isinstance(self.arguments, (tuple, list, Vector2D)):
                self.target(*self.arguments)
            else:
                self.target(self.arguments)

    def _Press(self):
        self.pressed = True
        self.time_of_press = CurrentTime()
        self.__CallTarget()

    def _Unpress(self):
        self.pressed = False

    def Update(self, shift=Vector2D(0, 0)):
        BaseElement.Update(self, shift)
        mouse_position = Vector2D(controls["mouse_position"]) - shift
        if (CurrentTime() -
                self.time_of_press) >= self.press_time and self.pressed:
            self._Unpress()
        relative = mouse_position - self.position
        in_position = 0 < relative.x < self.width and 0 < relative.y < self.height
        if controls.LeftClickDown:
            if in_position:
                self.focused = True
            else:
                self.focused = False
        if controls.LeftClickRelease:
            if in_position and self.focused and not self.pressed:
                self._Press()
            self.focused = False


class HoverButton(Button):
    def __init__(self,
                 text,
                 font,
                 target=None,
                 arguments=None,
                 padding=Vector2D(5, 5),
                 outline_size=Vector2D(2, 2),
                 background_colour=(200, 200, 200),
                 pressed_background_colour=(150, 150, 150),
                 outline_colour=(0, 0, 0),
                 text_colour=(0, 0, 0),
                 hover_background_colour=(200, 200, 200),
                 hover_outline_colour=(255, 255, 255),
                 hover_text_colour=(255, 255, 255),
                 press_time=0,
                 top_left_padding=None,
                 tooltip_info=[None, 2],
                 position=None,
                 is_active=True,
                 is_hidden=False):
        self.hover_background_colour = hover_background_colour
        self.hover_outline_colour = hover_outline_colour
        self.hover_text_colour = hover_text_colour
        self.hovering = False
        super().__init__(text, font, target, arguments, padding, outline_size,
                         background_colour, pressed_background_colour,
                         outline_colour, text_colour, press_time,
                         top_left_padding, tooltip_info, position, is_active,
                         is_hidden)

    def UpdateImage(self, update_size=True):
        super().UpdateImage(update_size)
        self.hover_image = pygame.Surface(tuple(self.size), pygame.SRCALPHA,
                                          32)
        self.hover_image.convert_alpha()
        self.hover_image.fill(self.hover_outline_colour)
        image_size = self.size - self.outline_size * 2
        smaller_hover_image = pygame.Surface(tuple(image_size),
                                             pygame.SRCALPHA, 32)
        smaller_hover_image.convert_alpha()
        smaller_hover_image.fill(self.hover_background_colour)
        text_label = self.font.render(self.text, 1, self.hover_text_colour)
        smaller_hover_image.blit(
            text_label,
            tuple(self.padding if self.top_left_padding is None else self.
                  top_left_padding))
        self.hover_image.blit(smaller_hover_image, tuple(self.outline_size))

    def Draw(self, surface, shift=Vector2D(0, 0), draw_end=None):
        if BaseElement.Draw(self, surface, shift, draw_end) == False:
            return False
        if self.pressed:
            image = self.pressed_image
        elif self.hovering:
            image = self.hover_image
        else:
            image = self.unpressed_image
        surface.blit(image, tuple(self.position + shift))

    def Update(self, shift=Vector2D(0, 0), needs_release=True):
        BaseElement.Update(self, shift)
        mouse_position = Vector2D(controls["mouse_position"]) - shift
        if (CurrentTime() -
                self.time_of_press) >= self.press_time and self.pressed:
            self._Unpress()
        relative = mouse_position - self.position
        in_position = 0 < relative.x < self.width and 0 < relative.y < self.height
        if controls.LeftClickDown:
            if in_position:
                if not needs_release and not self.pressed:
                    self._Press()
                else:
                    self.focused = True
            else:
                self.focused = False
        if controls.LeftClickRelease:
            if in_position and self.focused and not self.pressed:
                self._Press()
            self.focused = False
        self.hovering = in_position


class FixedHoverButton(HoverButton):
    def __init__(self,
                 text,
                 font,
                 size,
                 target=None,
                 arguments=None,
                 padding=Vector2D(5, 5),
                 outline_size=Vector2D(2, 2),
                 background_colour=(200, 200, 200),
                 pressed_background_colour=(150, 150, 150),
                 outline_colour=(0, 0, 0),
                 text_colour=(0, 0, 0),
                 hover_background_colour=(200, 200, 200),
                 hover_outline_colour=(255, 255, 255),
                 hover_text_colour=(255, 255, 255),
                 press_time=0,
                 top_left_padding=None,
                 tooltip_info=[None, 2],
                 position=None,
                 is_active=True,
                 is_hidden=False):
        self.size = size
        self.width = size.x
        self.height = size.y
        super().__init__(text, font, target, arguments, padding, outline_size,
                         background_colour, pressed_background_colour,
                         outline_colour, text_colour, hover_background_colour,
                         hover_outline_colour, hover_text_colour, press_time,
                         top_left_padding, tooltip_info, position, is_active,
                         is_hidden)

    def UpdateImage(self):
        super().UpdateImage(update_size=False)
        self.hover_image = pygame.Surface(tuple(self.size), pygame.SRCALPHA,
                                          32)
        self.hover_image.convert_alpha()
        self.hover_image.fill(self.hover_outline_colour)
        image_size = self.size - self.outline_size * 2
        smaller_hover_image = pygame.Surface(tuple(image_size),
                                             pygame.SRCALPHA, 32)
        smaller_hover_image.convert_alpha()
        smaller_hover_image.fill(self.hover_background_colour)
        text_label = self.font.render(self.text, 1, self.hover_text_colour)
        smaller_hover_image.blit(
            text_label,
            tuple(self.padding if self.top_left_padding is None else self.
                  top_left_padding))
        self.hover_image.blit(smaller_hover_image, tuple(self.outline_size))

    def Draw(self,
             surface,
             shift=Vector2D(0, 0),
             draw_end=None,
             force_hover=None):
        if force_hover != None:
            prev_hover = self.hovering
            self.hovering = force_hover
            result = super().Draw(surface, shift=shift, draw_end=None)
            self.hovering = prev_hover
            return result
        return super().Draw(surface, shift=shift, draw_end=draw_end)


def InvertColour(r, g, b):
    return (255 - r, 255 - g, 255 - b)


class Entry(BaseElement):
    def __init__(self,
                 font,
                 width,
                 initial_key_time=0.4,
                 key_time=0.04,
                 padding=Vector2D(5, 5),
                 outline_size=Vector2D(2, 2),
                 initial_text="",
                 empty_text="",
                 hide_text=False,
                 text_colour=(0, 0, 0),
                 empty_text_colour=(140, 140, 140),
                 background_colour=(200, 200, 200),
                 outline_colour=(0, 0, 0),
                 history_range=500,
                 tooltip_info=[None, 2],
                 position=None,
                 is_active=True,
                 is_hidden=False):
        super().__init__(position, is_active, is_hidden, *tooltip_info)
        self.history_range = history_range
        self.history = [None] * self.history_range
        self.future = [None] * self.history_range
        self.text = initial_text
        self.max_text_width = width - (outline_size.x + padding.x) * 2
        self.display_text = ''
        self.display_index = 0
        self.font = font
        self.width = width
        self.font_height = self.font.size("ABCDEFGHIJKLMNOPQRSTUVWXYZ")[
            1]  # TODO check if still needed?
        self.height = self.font_height + (padding.y + outline_size.y) * 2
        self.size = Vector2D(self.width, self.height)
        self.hide_text = hide_text
        self.cursor_index = 0
        self.UpdateText()
        self.font = font
        self.background_colour = background_colour
        self.outline_colour = outline_colour
        self.text_colour = text_colour
        self.padding = padding
        self.outline_size = outline_size
        self.image = None
        self.UpdateImage()
        self.is_focused = False
        self.initial_key_time = initial_key_time
        self.key_time = key_time
        self.time_of_key_press = 0
        self.key_count = 0
        self.time_of_cursor = 0
        self.cursor_enabled = True
        self.drag_select_index = 0
        self.current_key_name = None
        self.current_key_unicode = None
        self.shift_pressed = 0
        self.ctrl_pressed = 0
        self.made_selection_replacement = False
        self.time_of_last_scroll = 0
        self.scroll_time = 0.05
        self.empty_text = empty_text
        self.empty_text_colour = empty_text_colour

    def ClearHistoryAndFuture(self):
        self.history = [None] * self.history_range
        self.future = [None] * self.history_range

    def UpdateTextHistory(self):
        # wipe future, move histories back, add text to history
        for i in range(self.history_range - 1):
            self.history[i] = self.history[i + 1]
        self.history[self.history_range - 1] = self.text
        self.future = [None] * self.history_range

    def Undo(self):
        # move all futures forward by 1, add text to future,
        # add last history to text, move all histories forward by 1
        if self.history[self.history_range - 1] == None:
            return
        for i in range(self.history_range - 1):
            self.future[self.history_range - 1 -
                        i] = self.future[self.history_range - 2 - i]
        self.future[0] = self.text
        self.text = self.history[self.history_range - 1]
        for i in range(self.history_range - 1):
            self.history[self.history_range - 1 -
                         i] = self.history[self.history_range - 2 - i]
        self.history[0] = None
        self.drag_select_index = None
        self.UpdateText()

    def Redo(self):
        # move all histories backward by 1, last history is text,
        # set text to first future, move all futures backward by 1
        if self.future[0] == None:
            return
        for i in range(self.history_range - 1):
            self.history[i] = self.history[i + 1]
        self.history[self.history_range - 1] = self.text
        self.text = self.future[0]
        for i in range(self.history_range - 1):
            self.future[i] = self.future[i + 1]
        self.future[self.history_range - 1] = None
        self.drag_select_index = None
        self.UpdateText()

    def UpdateText(self, text=None):
        if text is not None:
            self.text = text
        if self.hide_text:
            display_text = "*" * len(self.text)
        else:
            display_text = self.text
        if self.cursor_index < self.display_index:
            self.display_index = self.cursor_index
            if self.cursor_index > 0 and self.made_selection_replacement:
                self.made_selection_replacement = False
                self.display_index -= 1
        self.display_text = ''
        if self.font.size(
                display_text[self.display_index:])[0] <= self.max_text_width:
            self.display_text = display_text[self.display_index:]
            return
        i = len(display_text) - 1
        while self.font.size(display_text[self.display_index:i +
                                          1])[0] > self.max_text_width:
            i -= 1
        self.display_text = display_text[self.display_index:i + 1]
        if self.cursor_index > i:
            i = self.cursor_index
            while self.font.size(display_text[i:self.cursor_index +
                                              1])[0] < self.max_text_width:
                i -= 1
            i += 1
            self.display_index = i
            self.display_text = display_text[i:self.cursor_index + 1]

    def UpdateImage(self):
        if self.outline_colour == 'TRANSPARENT' or self.background_colour == 'TRANSPARENT':
            self.image = pygame.Surface(tuple(self.size), pygame.SRCALPHA, 32)
            self.image.convert_alpha()
            if self.outline_colour != 'TRANSPARENT':
                vertical = pygame.Surface((self.outline_size.x, self.height))
                vertical.fill(self.outline_colour)
                horizontal = pygame.Surface((self.width, self.outline_size.y))
                horizontal.fill(self.outline_colour)
                self.image.blit(vertical, [0, 0])
                self.image.blit(vertical,
                                [self.width - self.outline_size.x, 0])
                self.image.blit(horizontal, [0, 0])
                self.image.blit(horizontal,
                                [0, self.height - self.outline_size.y])
        else:
            self.image = pygame.Surface(tuple(self.size))
            self.image.fill(self.outline_colour)
        if self.background_colour == 'TRANSPARENT':
            background_image = pygame.Surface(
                tuple(self.size - self.outline_size * 2), pygame.SRCALPHA, 32)
            background_image.convert_alpha()
        else:
            background_image = pygame.Surface(
                tuple(self.size - self.outline_size * 2))
            background_image.fill(self.background_colour)
        self.image.blit(background_image, tuple(self.outline_size))
        self.cursor_image = pygame.Surface((2, int(self.font_height / 10 * 7)))
        self.cursor_image.fill(self.text_colour)

    def Draw(self, surface, shift=Vector2D(0, 0), draw_end=None):
        if super().Draw(surface, shift, draw_end) == False:
            return False
        surface.blit(self.image, tuple(self.position + shift))
        label_padding = self.outline_size + self.padding + shift
        if self.text == '':
            label = self.font.render(self.empty_text, 1,
                                     self.empty_text_colour)
        else:
            label = self.font.render(self.display_text, 1, self.text_colour)
        surface.blit(label, tuple(self.position + label_padding))
        if self.is_focused:
            if self.drag_select_index != None and self.drag_select_index != self.cursor_index:
                if self.cursor_index > self.drag_select_index:
                    min_index = self.drag_select_index
                    max_index = self.cursor_index - 1
                else:
                    min_index = self.cursor_index
                    max_index = self.drag_select_index - 1
                min_index -= self.display_index
                max_index -= self.display_index
                if min_index < 0:
                    min_index = 0
                upper_index = len(self.display_text)
                if max_index > upper_index:
                    max_index = upper_index
                start_pos = self.font.size(self.display_text[:min_index])[0]
                end_pos = self.font.size(self.display_text[:max_index + 1])[0]
                # not exactly the same as per subtraction therefore necessary.
                highlight_size = self.font.size(
                    self.display_text[min_index:max_index + 1])[0]
                highlight = pygame.Surface(
                    (highlight_size, self.font_height - self.padding.y))
                highlight.fill((0, 120, 215))
                surface.blit(
                    highlight,
                    tuple(self.position + label_padding +
                          Vector2D(start_pos, 0)))
                h_label = self.font.render(
                    self.display_text[min_index:max_index + 1], 1,
                    InvertColour(*self.text_colour))
                surface.blit(
                    h_label,
                    tuple(self.position + label_padding +
                          Vector2D(end_pos - highlight_size, 0)))
            if self.cursor_enabled:
                target_index = self.cursor_index - self.display_index
                if target_index > 0:
                    cursor_position = self.font.size(
                        self.display_text[:target_index])[0]
                else:
                    cursor_position = 0
                cursor_position = label_padding + Vector2D(
                    cursor_position, self.font_height // 20 * 3)
                surface.blit(self.cursor_image,
                             tuple(self.position + cursor_position))
            if (CurrentTime() - self.time_of_cursor) > 0.5:
                self.cursor_enabled = not self.cursor_enabled
                self.time_of_cursor = CurrentTime()

    def GetCurrentCursorIndex(self, relative_position):
        relative_position -= self.outline_size
        relative_position -= self.padding
        for i in range(1, len(self.display_text) + 1):
            text_width = self.font.size(self.display_text[:i])[0]
            if text_width > relative_position.x:
                return i - 1 + self.display_index
        return None

    def findNextBreak(self, index, direction):
        text_len = len(self.text)
        while text_len > index > 0:
            if self.text[index] in [' ', '-', '_', '.', ',']:
                return index
            index += direction
        return index

    def DoKeyPress(self, name, unicode):
        if name == "escape":
            self.is_focused = False
        elif name == "backspace":
            if self.drag_select_index != None:
                if controls["mouse_pressed"][0]:
                    return
                self.UpdateTextHistory()
                lower_index = min(self.drag_select_index, self.cursor_index)
                upper_index = max(self.drag_select_index, self.cursor_index)
                self.text = self.text[:lower_index] + self.text[upper_index:]
                self.cursor_index = lower_index
                self.drag_select_index = None
            elif self.cursor_index > 0:
                self.UpdateTextHistory()
                self.text = self.text[:self.cursor_index -
                                      1] + self.text[self.cursor_index:]
                self.cursor_index -= 1
                if self.display_index > 0:
                    self.display_index -= 1
                if self.cursor_index == 0:
                    self.cursor_enabled = True
                    self.time_of_cursor = CurrentTime()
        elif name == "left shift":
            self.shift_pressed += 1
        elif name == "right shift":
            self.shift_pressed += 1
        elif name == "left ctrl":
            self.ctrl_pressed += 1
        elif name == "right ctrl":
            self.ctrl_pressed += 1
        elif name == "left":
            if self.drag_select_index != None:
                if self.shift_pressed == 0:
                    if self.drag_select_index < self.cursor_index:
                        self.cursor_index = self.drag_select_index
                    self.drag_select_index = None
                    if self.ctrl_pressed:
                        if self.cursor_index < 2:
                            self.cursor_index = 0
                        else:
                            self.cursor_index = self.findNextBreak(
                                self.cursor_index - 2, -1)
                            if 0 < self.cursor_index:
                                self.cursor_index += 1
                elif self.cursor_index > 0:
                    self.cursor_index -= 1
                    if self.ctrl_pressed:
                        if self.cursor_index < 1:
                            self.cursor_index = 0
                        else:
                            self.cursor_index = self.findNextBreak(
                                self.cursor_index - 1, -1)
                            if 0 < self.cursor_index:
                                self.cursor_index += 1
            elif self.cursor_index > 0:
                if self.shift_pressed != 0:
                    self.drag_select_index = self.cursor_index
                self.cursor_index -= 1
                if self.ctrl_pressed:
                    if self.cursor_index < 1:
                        self.cursor_index = 0
                    else:
                        self.cursor_index = self.findNextBreak(
                            self.cursor_index - 1, -1)
                        if 0 < self.cursor_index:
                            self.cursor_index += 1
            self.cursor_enabled = True
            self.time_of_cursor = CurrentTime()
        elif name == "right":
            if self.drag_select_index != None:
                if self.shift_pressed == 0:
                    if self.drag_select_index > self.cursor_index:
                        self.cursor_index = self.drag_select_index
                    self.drag_select_index = None
                    if self.ctrl_pressed:
                        if self.cursor_index != len(self.text):
                            self.cursor_index = self.findNextBreak(
                                self.cursor_index + 1, 1)
                            if len(self.text) > self.cursor_index:
                                self.cursor_index += 1
                elif self.cursor_index < len(self.text):
                    self.cursor_index += 1
                    if self.ctrl_pressed:
                        self.cursor_index = self.findNextBreak(
                            self.cursor_index, 1)
                        if len(self.text) > self.cursor_index:
                            self.cursor_index += 1
            elif self.cursor_index < len(self.text):
                if self.shift_pressed != 0:
                    self.drag_select_index = self.cursor_index
                self.cursor_index += 1
                if self.ctrl_pressed:
                    self.cursor_index = self.findNextBreak(
                        self.cursor_index, 1)
                    if len(self.text) > self.cursor_index:
                        self.cursor_index += 1
            self.cursor_enabled = True
            self.time_of_cursor = CurrentTime()
        elif name not in [
                "backspace", "enter", "return", "left", "right", "left shift",
                "right shift", "left ctrl", "right ctrl", "up", "down",
                "left alt", "right alt", "caps lock", "tab"
        ]:
            if self.ctrl_pressed:
                if name == "a":
                    self.drag_select_index = 0
                    self.cursor_index = len(self.text)
                elif name == "c" and self.drag_select_index != None:
                    lower_index = min(self.drag_select_index,
                                      self.cursor_index)
                    upper_index = max(self.drag_select_index,
                                      self.cursor_index)
                    CopyToClipboard(self.text[lower_index:upper_index + 1])
                elif name == "v":
                    pasted_text = PasteFromClipboard()
                    if len(pasted_text) == 0:
                        return
                    if self.drag_select_index != None:
                        if controls["mouse_pressed"][0]:
                            return
                        self.UpdateTextHistory()
                        lower_index = min(self.drag_select_index,
                                          self.cursor_index)
                        upper_index = max(self.drag_select_index,
                                          self.cursor_index)
                        self.text = self.text[:lower_index] + self.text[
                            upper_index:]
                        self.cursor_index = lower_index
                        self.drag_select_index = None
                        self.made_selection_replacement = True
                    else:
                        self.UpdateTextHistory()
                    self.text = self.text[:self.
                                          cursor_index] + pasted_text + self.text[
                                              self.cursor_index:]
                    self.cursor_index += len(pasted_text)
                    self.key_count += 1
                elif name == "z":
                    self.Undo()
                    self.key_count += 1
                elif name == "y":
                    self.Redo()
                    self.key_count += 1
                self.cursor_enabled = True
                self.time_of_cursor = CurrentTime()
                return
            if self.drag_select_index != None:
                if controls["mouse_pressed"][0]:
                    return
                self.UpdateTextHistory()
                lower_index = min(self.drag_select_index, self.cursor_index)
                upper_index = max(self.drag_select_index, self.cursor_index)
                self.text = self.text[:lower_index] + unicode + self.text[
                    upper_index:]
                self.cursor_index = lower_index + 1
                self.drag_select_index = None
                self.made_selection_replacement = True
            else:
                self.UpdateTextHistory()
                self.made_selection_replacement = False
                self.text = self.text[:self.
                                      cursor_index] + unicode + self.text[
                                          self.cursor_index:]
                self.cursor_index += 1
            self.cursor_enabled = True
            self.time_of_cursor = CurrentTime()
        self.key_count += 1

    def Unfocus(self):
        self.current_key_name = None
        self.current_key_unicode = None
        self.key_count = 0
        self.shift_pressed = 0
        self.ctrl_pressed = 0
        self.drag_select_index = None
        self.ClearHistoryAndFuture()

    def Reset(self):
        self.cursor_index = 0
        self.UpdateText('')
        self.Unfocus()

    def Update(self, shift=Vector2D(0, 0)):
        if super().Update(shift) == False:
            return False
        was_focused = self.is_focused
        mouse_position = Vector2D(controls["mouse_position"]) - shift
        if controls.LeftClickDown:
            relative_position = mouse_position - self.position
            self.is_focused = 0 < relative_position.x < self.width and \
                              0 < relative_position.y < self.height
            if self.is_focused:
                cursor_index = self.GetCurrentCursorIndex(relative_position)
                if cursor_index == None:
                    self.cursor_index = self.display_index + len(
                        self.display_text)
                else:
                    self.cursor_index = cursor_index
                self.drag_select_index = None
                self.cursor_enabled = True
                self.time_of_cursor = CurrentTime()
        elif controls["mouse_pressed"][0] and self.is_focused:
            if self.drag_select_index == None:
                self.drag_select_index = self.cursor_index
            self.cursor_index = self.GetCurrentCursorIndex(mouse_position -
                                                           self.position)
            if self.cursor_index == None:
                if mouse_position.x > (self.position.x + self.width):
                    self.cursor_index = self.display_index + len(
                        self.display_text)
                    end_index = self.display_index + len(self.display_text)
                    if end_index < len(self.text) and (CurrentTime(
                    ) - self.time_of_last_scroll) > 0.25 * self.width * (
                            self.scroll_time /
                        (mouse_position.x - self.position.x - self.width)):
                        self.cursor_index += 1
                        self.time_of_last_scroll = CurrentTime()
                        self.UpdateText()
                else:
                    self.cursor_index = self.display_index + len(
                        self.display_text)
            if self.cursor_index == self.display_index and \
                mouse_position.x < self.position.x and \
                self.cursor_index != 0:
                if (CurrentTime() -
                        self.time_of_last_scroll) > 0.25 * self.width * (
                            self.scroll_time /
                            (self.position.x - mouse_position.x)):
                    self.cursor_index -= 1
                    self.time_of_last_scroll = CurrentTime()
                    self.UpdateText()
            if self.cursor_index == self.drag_select_index:
                self.drag_select_index = None
        if self.is_focused:
            if self.current_key_name != None:
                for event in controls["events"]:
                    if event.type == pygame.KEYUP:
                        key = pygame.key.name(event.key)
                        if key == self.current_key_name:
                            self.current_key_name = None
                            self.current_key_unicode = None
                            self.key_count = 0
                if self.current_key_name != None and self.current_key_name not in [
                        "left shift", "right shift", "left ctrl", "right ctrl"
                ]:
                    key_time = self.initial_key_time if self.key_count == 1 else self.key_time
                    time_since_last_key = CurrentTime(
                    ) - self.time_of_key_press
                    if time_since_last_key >= key_time:
                        self.time_of_key_press = CurrentTime()
                        self.DoKeyPress(self.current_key_name,
                                        self.current_key_unicode)
                        self.UpdateText()
            for event in controls["events"]:
                if event.type == pygame.KEYDOWN:
                    self.time_of_key_press = CurrentTime()
                    self.key_count = 0
                    self.current_key_name = pygame.key.name(event.key)
                    if event.mod & pygame.KMOD_CTRL:
                        self.current_key_unicode = self.current_key_name
                    else:
                        self.current_key_unicode = event.unicode
                    self.DoKeyPress(self.current_key_name,
                                    self.current_key_unicode)
                    self.UpdateText()
            for event in controls["events"]:
                if event.type == pygame.KEYUP:
                    key = pygame.key.name(event.key)
                    if key == "left shift" and self.shift_pressed > 0:
                        self.shift_pressed -= 1
                    elif key == "right shift" and self.shift_pressed > 0:
                        self.shift_pressed -= 1
                    elif key == "left ctrl" and self.ctrl_pressed > 0:
                        self.ctrl_pressed -= 1
                    elif key == "right ctrl" and self.ctrl_pressed > 0:
                        self.ctrl_pressed -= 1
        if was_focused and not self.is_focused:
            self.Unfocus()

    def WithinBoundingBox(self, coord1, coord2):
        corners = [
            self.position, self.position + self.size,
            self.position + Vector2D(self.width, 0),
            self.position + Vector2D(0, self.height)
        ]
        for corner in corners:
            if CoordInBoundingBox(corner, coord1, coord2):
                return True
        return CoordInBoundingBox(coord1, corners[0],
                                  corners[1])  # if 1 coord of bounding box
        # is in the label, and it hasn't been detected yet, the bounding box is contained within
        # the label


class FunctionalEntry(Entry):
    def __init__(self,
                 font,
                 width,
                 target,
                 arguments=None,
                 send_text=True,
                 initial_key_time=0.4,
                 key_time=0.04,
                 padding=Vector2D(5, 5),
                 outline_size=Vector2D(2, 2),
                 initial_text="",
                 empty_text="",
                 hide_text=False,
                 text_colour=(0, 0, 0),
                 empty_text_colour=(140, 140, 140),
                 background_colour=(200, 200, 200),
                 outline_colour=(0, 0, 0),
                 history_range=500,
                 tooltip_info=[None, 2],
                 position=None,
                 is_active=True,
                 is_hidden=False):
        super().__init__(font, width, initial_key_time, key_time, padding,
                         outline_size, initial_text, empty_text, hide_text,
                         text_colour, empty_text_colour, background_colour,
                         outline_colour, history_range, tooltip_info, position,
                         is_active, is_hidden)
        self.target = target
        self.arguments = arguments
        self.send_text = send_text
        self.send_history = [None] * self.history_range
        self.temp_send_history = [None] * self.history_range
        self.temp_send_future = [None] * self.history_range

    def ClearSendHistoryAndFuture(self):
        self.temp_send_history = [None] * self.history_range
        self.temp_send_future = [None] * self.history_range

    def UpdateSendHistory(self):
        for i in range(self.history_range - 1):
            self.send_history[i] = self.send_history[i + 1]
        self.send_history[self.history_range - 1] = self.text
        self.temp_send_history = [c for c in self.send_history]
        self.temp_send_future = [None] * self.history_range

    def LoadLastSend(self):
        if self.temp_send_history[self.history_range - 1] == None:
            return
        for i in range(self.history_range - 1):
            self.temp_send_future[self.history_range - 1 -
                                  i] = self.temp_send_future[self.history_range
                                                             - 2 - i]
        self.temp_send_future[0] = self.text
        self.text = self.temp_send_history[self.history_range - 1]
        for i in range(self.history_range - 1):
            self.temp_send_history[self.history_range - 1 -
                                   i] = self.temp_send_history[
                                       self.history_range - 2 - i]
        self.temp_send_history[0] = None
        self.drag_select_index = None
        self.cursor_index = len(self.text)
        self.cursor_enabled = True
        self.time_of_cursor = CurrentTime()
        self.UpdateText()

    def LoadNextSend(self):
        if self.temp_send_future[0] == None:
            return
        for i in range(self.history_range - 1):
            self.temp_send_history[i] = self.temp_send_history[i + 1]
        self.temp_send_history[self.history_range - 1] = self.text
        self.text = self.temp_send_future[0]
        for i in range(self.history_range - 1):
            self.temp_send_future[i] = self.temp_send_future[i + 1]
        self.temp_send_future[self.history_range - 1] = None
        self.drag_select_index = None
        self.cursor_index = len(self.text)
        self.cursor_enabled = True
        self.time_of_cursor = CurrentTime()
        self.UpdateText()

    def TriggerTarget(self):
        args = []
        if self.arguments != None:
            if isinstance(self.arguments, (tuple, list, Vector2D)):
                args += list(self.arguments)
            else:
                args.append(self.arguments)
        if self.send_text:
            args.append(self.text)
        self.target(*args)

    def Reset(self):
        super().Reset()
        self.ClearSendHistoryAndFuture()

    def DoKeyPress(self, name, unicode):
        super().DoKeyPress(name, unicode)
        if name == "up":
            self.LoadLastSend()
        elif name == "down":
            self.LoadNextSend()

    def Update(self, shift=Vector2D(0, 0), do_clear=True):
        if super().Update(shift) == False:
            return False
        if self.is_focused:
            for event in controls["events"]:
                if event.type == pygame.KEYDOWN and pygame.key.name(
                        event.key) == "return" and self.text != '':
                    self.UpdateSendHistory()
                    self.TriggerTarget()
                    if do_clear:
                        self.text = ''
                        self.cursor_index = 0
                        self.UpdateText()
                        self.Unfocus()
                    break


class UnfocusEntry(FunctionalEntry):
    def Update(self, shift=Vector2D(0, 0)):
        was_focused = self.is_focused
        Entry.Update(self, shift)
        if not self.is_focused and was_focused:  # i.e. unfocused
            self.TriggerTarget()


class ConstantFunctionalEntry(FunctionalEntry):
    def Update(self, shift=Vector2D(0, 0)):
        prev_text = self.text
        Entry.Update(self, shift)
        if self.text != prev_text:
            self.TriggerTarget()


class Element:
    def __init__(self,
                 visual_object,
                 positioning,
                 position_from=Vector2D(0.5, 0.5)):
        self.visual_object = visual_object
        self.box_location = Vector2D(0, 0)
        self.positioning = positioning
        self.position_from = position_from
        self.padding = Vector2D(0, 0)
        self.container_size = Vector2D(0, 0)
        self.active = True
        self.hidden = False

    def __str__(self):
        return str(self.visual_object)

    def SetObjectActive(self, new_value):
        self.visual_object.active = new_value

    def SetObjectHidden(self, new_value):
        self.visual_object.hidden = new_value

    def UpdatePadding(self):
        self.padding = ScalePosition(Vector2D(0, 0),
                                     self.container_size,
                                     self.positioning,
                                     object_size=self.size,
                                     scale_from=self.position_from)

    def Draw(self, surface, shift=Vector2D(0, 0), draw_end=None):
        if self.visual_object == None or self.hidden:
            return
        padding = shift + self.box_location + self.padding
        self.visual_object.Draw(surface, shift=padding, draw_end=draw_end)

    def Update(self, shift=Vector2D(0, 0)):
        if self.visual_object == None or not self.active:
            return
        padding = shift + self.box_location + self.padding
        self.visual_object.Update(shift=padding)

    @property
    def size(self):
        return self.visual_object.size


class Container(BaseElement):
    def __init__(self,
                 columns,
                 rows,
                 edge_padding=Vector2D(0, 0),
                 inner_padding=Vector2D(15, 15),
                 has_outline=False,
                 position=None,
                 is_active=True,
                 is_hidden=False):
        super().__init__(position, is_active, is_hidden)
        self.elements = []
        for i in range(rows):
            row = []
            for j in range(columns):
                row.append(Element(None, Vector2D(0, 0)))
            self.elements.append(row)
        self.columns = columns
        self.rows = rows
        self.has_outline = has_outline
        self.edge_padding = edge_padding
        self.inner_padding = inner_padding

    def Clear(self):
        self.elements = []
        for i in range(self.rows):
            row = []
            for j in range(self.columns):
                row.append(Element(None, Vector2D(0, 0)))
            self.elements.append(row)
        self.UpdateElementBoxes()
        self.UpdatePaddings()

    def CheckIndexValidity(self, x_index, y_index):
        if not (isinstance(x_index, int) and isinstance(y_index, int)):
            return False
        return 0 <= x_index < self.columns and 0 <= y_index < self.rows

    def DisplayInText(self):
        for row in self.elements:
            print(" ".join([str(element) for element in row]))

    def UpdateImage(self):
        for row in self.elements:
            for element in row:
                if element.visual_object is not None:
                    element.visual_object.UpdateImage()

    def UpdateElementLocations(self):
        cumulative_h = self.edge_padding.y
        for i in range(0, self.rows):
            cumulative_w = self.edge_padding.x
            for j in range(self.columns):
                element = self.elements[i][j]
                element.box_location = Vector2D(cumulative_w, cumulative_h)
                cumulative_w += element.container_size.x + self.inner_padding.x
            cumulative_h += element.container_size.y + self.inner_padding.y

    def UpdatePaddings(self):
        for row in self.elements:
            for element in row:
                if element.visual_object is not None:
                    element.UpdatePadding()

    def UpdateElementBoxes(self):
        container_sizes = []
        for i in range(self.rows):
            row = []
            for j in range(self.columns):
                row.append(Vector2D(0, 0))
            container_sizes.append(row)
        for index, row in enumerate(
                self.elements):  # set element height to max in row.
            element_sizes = [
                0 if element.visual_object is None else element.size.y
                for element in row
            ]
            max_height_in_row = max(element_sizes)
            for size in container_sizes[index]:
                size.y = max_height_in_row
        for i in range(0, self.columns):  # set element width to max in column.
            element_sizes = []
            for j in range(0, self.rows):
                element_sizes.append(0 if self.elements[j][i].visual_object is
                                     None else self.elements[j][i].size.x)
            max_width_in_column = max(element_sizes)
            for j in range(0, self.rows):
                container_sizes[j][i].x = max_width_in_column
        for i in range(0, self.rows):
            for j in range(self.columns):
                self.elements[i][j].container_size = container_sizes[i][j]
        self.UpdateElementLocations()

    def AddElement(self,
                   item,
                   x_index=None,
                   y_index=None,
                   positioning=Vector2D(0.5, 0.5),
                   position_from=Vector2D(0.5, 0.5)):
        element = Element(item, positioning, position_from=position_from)
        if x_index is not None and y_index is not None:
            if not self.CheckIndexValidity(x_index, y_index):
                print("That is not a valid position. The element cannot be " + \
                      "added to the container.")
                return
            removed_item = self.elements[y_index][x_index]
            self.elements[y_index][x_index] = None
            del removed_item  # deletes current element at that index.
            self.elements[y_index][x_index] = element
        else:
            changed = False
            for i in range(0, self.rows):
                for j in range(0, self.columns):
                    if self.elements[i][j].visual_object is None:
                        self.elements[i][j] = element
                        changed = True
                        break
                if changed:
                    break
            if not changed:
                print("Container is full. Unable to add UI element.")
        # update the box sizes and padding with the new element added.
        self.UpdateElementBoxes()
        self.UpdatePaddings()

    def AddElements(self, *args):
        for arg in args:
            if isinstance(arg, (list, tuple)):
                positioning = arg[1]
                position_from = arg[2]
                element = arg[0]
                self.AddElement(element,
                                positioning=positioning,
                                position_from=position_from)
            else:
                element = arg
                self.AddElement(element)

    def RemoveElement(self, item=None, x_index=None, y_index=None):
        if item is not None:
            for i in range(0, self.rows):
                for j in range(0, self.columns):
                    if self.elements[i][j].visual_object is item:
                        self.elements[i][j] = Element(None, Vector2D(0, 0))
                        return
            print("UI element not found in container. Cannot remove element.")
        else:
            if x_index is None or y_index is None:
                print(
                    "No valid information was input to use to remove an element. You must either input a y-index value\n"
                    + "and an x-index value or the visual object to delete.")
                return
            if not self.CheckIndexValidity(x_index, y_index):
                print(
                    "That is not a valid position. There is no element to remove from the container."
                )
                return
            self.elements[y_index][x_index] = Element(None, Vector2D(0, 0))
        # does not update element box sizes, positions or padding unless
        # specifically told to as this is not necessary

    def Draw(self, surface, shift=Vector2D(0, 0), draw_end=None):
        if super().Draw(surface, shift) == False:
            return False
        for row in self.elements:
            for element in row:
                element.Draw(surface,
                             shift=(shift + self.position),
                             draw_end=draw_end)
        if self.has_outline:
            pos = self.position + shift
            positions = [
                tuple(pos), (pos.x + self.size.x, pos.y),
                tuple(pos + self.size), (pos.x, pos.y + self.size.y)
            ]
            pygame.draw.polygon(surface, (0, 0, 0), positions, 1)

    def Update(self, shift=Vector2D(0, 0)):
        if super().Update(shift) == False:
            return False
        element_padding = shift + self.position
        for row in self.elements:
            for element in row:
                element.Update(shift=element_padding)

    @property
    def size(self):
        total_width = 0
        total_height = 0
        for i in range(0, self.columns):
            widths = []
            for j in range(0, self.rows):
                element = self.elements[j][i]
                widths.append(element.container_size.x if element.
                              visual_object is not None else 0)
            total_width += max(
                widths
            )  # finds and adds up the maximum width for each column of visual elements
        for row in self.elements:
            total_height += max([(element.container_size.y
                                  if element.visual_object is not None else 0)
                                 for element in row])
            # finds and adds up the maximum height for each row
        size = Vector2D(total_width, total_height)
        # add any inner and edge padding size values.
        size += self.edge_padding * 2
        size.x += self.inner_padding.x * (self.columns - 1)
        size.y += self.inner_padding.y * (self.rows - 1)
        return size

    @property
    def width(self):
        return self.size.x

    @property
    def height(self):
        return self.size.y

    def WithinBoundingBox(self, coord1, coord2):
        corners = [
            self.position, self.position + self.size,
            self.position + Vector2D(self.columns, 0),
            self.position + Vector2D(0, self.rows)
        ]
        for corner in corners:
            if CoordInBoundingBox(corner, coord1, coord2):
                return True
        return CoordInBoundingBox(coord1, corners[0],
                                  corners[1])  # if 1 coord of bounding box
        # is in the label, and it hasn't been detected yet, the bounding box is contained within
        # the label


class RegulatedContainer(Container):
    def __init__(self,
                 columns,
                 rows,
                 edge_padding=Vector2D(0, 0),
                 inner_padding=Vector2D(15, 15),
                 has_outline=False,
                 position=None,
                 is_active=True,
                 is_hidden=False):
        super().__init__(columns, rows, edge_padding, inner_padding,
                         has_outline, position, is_active, is_hidden)

    def GetElementToUpdate(self, shift):
        mouse_position = Vector2D(
            controls["mouse_position"]) - shift - self.position
        i = 0
        while i < self.rows and self.elements[i][
                0].box_location.y < mouse_position.y:
            i += 1
        if i == 0:
            return None  # mouse is not there so you don't need to update
        i -= 1
        j = 0
        while j < self.columns and self.elements[i][
                j].box_location.x < mouse_position.x:
            j += 1
        if j == 0:
            return None
        j -= 1
        return self.elements[i][j]

    def Draw(self, surface, shift=Vector2D(0, 0), draw_end=None):
        BaseElement.Draw(self, surface, shift)
        for row in self.elements:
            for element in row:
                if element.active:
                    element.Draw(surface,
                                 shift=(shift + self.position),
                                 draw_end=draw_end)
                else:
                    element.Draw(surface, shift=(shift + self.position))
        if self.has_outline:
            pos = self.position + shift
            positions = [
                tuple(pos), (pos.x + self.size.x, pos.y),
                tuple(pos + self.size), (pos.x, pos.y + self.size.y)
            ]
            pygame.draw.polygon(surface, (0, 0, 0), positions, 1)

    def Update(self, shift):
        if BaseElement.Update(self, shift) == False:
            return False
        e = self.GetElementToUpdate(shift)
        if e != None:
            e.active = True
            e.Update(shift=shift + self.position)
        for row in self.elements:
            for element in row:
                if element != e:
                    element.active = False


class ScrollingRegulatedContainer(RegulatedContainer):
    def __init__(self,
                 columns,
                 rows,
                 scroll_update_func,
                 edge_padding=Vector2D(0, 0),
                 inner_padding=Vector2D(15, 15),
                 has_outline=False,
                 position=None,
                 is_active=True,
                 is_hidden=False):
        super().__init__(columns, rows, edge_padding, inner_padding,
                         has_outline, position, is_active, is_hidden)
        self.scroll_update = scroll_update_func
        self.current_row = 0
        self.min_row = 0
        self.max_row = rows

    def Update(self, shift):
        mouse_position = Vector2D(
            controls["mouse_position"]) - self.position - shift
        if 0 < mouse_position.x < self.width and 0 < mouse_position.y < self.height:
            for event in controls["events"]:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 5 and self.current_row < self.max_row:
                        self.current_row += 1
                        self.scroll_update()
                    elif event.button == 4 and self.current_row > self.min_row:
                        self.current_row -= 1
                        self.scroll_update()
        return super().Update(shift)


class RatingsBar(BaseElement):
    def __init__(self,
                 base_image,
                 alternate_image,
                 size,
                 min_rating=0,
                 max_rating=10,
                 padding=Vector2D(10, 10),
                 outline_size=Vector2D(5, 5),
                 outline_colour=(0, 0, 0),
                 background_colour=(200, 200, 200),
                 tooltip_info=[None, 2],
                 position=None,
                 is_active=True,
                 is_hidden=False):
        super().__init__(position, is_active, is_hidden, *tooltip_info)
        self.base_image = base_image
        self.scaled_base = None
        self.alternate_image = alternate_image
        self.scaled_alternate = None
        self.size = size
        self.width = self.size.x
        self.height = self.size.y
        self.min_rating = min_rating
        self.max_rating = max_rating
        self.rating = min_rating
        self.padding = padding
        self.outline_size = outline_size
        self.unpadded_size = Vector2D(0, 0)
        self.outline_colour = outline_colour
        self.background_colour = background_colour
        self.background_image = None
        self.image = None
        self.image_width = 0
        self.UpdateImageInformation()
        self.UpdateImage()

    def UpdateImage(self):
        self.image = self.background_image.copy()
        self.image.convert_alpha()
        x_pos = self.outline_size.x + self.padding.x
        y_pos = self.outline_size.y + self.padding.y
        for i in range(0, self.max_rating):
            if i < self.rating:
                self.image.blit(self.scaled_alternate,
                                (int(x_pos), int(y_pos)))
            else:
                self.image.blit(self.scaled_base, (int(x_pos), int(y_pos)))
            x_pos += self.padding.x + self.image_width

    def UpdateImageInformation(self):
        self.unpadded_size = self.size - 2 * (self.outline_size + self.padding)
        self.background_image = pygame.Surface(tuple(self.size),
                                               pygame.SRCALPHA, 32)
        self.background_image.convert_alpha()
        self.background_image.fill(self.outline_colour)
        smaller_image = pygame.Surface(
            tuple(self.size - 2 * self.outline_size), pygame.SRCALPHA, 32)
        smaller_image.convert_alpha()
        smaller_image.fill(self.background_colour)
        self.background_image.blit(smaller_image, tuple(self.outline_size))
        image_size = self.unpadded_size.copy()
        image_size.x -= (self.max_rating - 1) * self.padding.x
        image_size.x /= self.max_rating
        self.image_width = image_size.x
        self.scaled_base = pygame.transform.scale(
            self.base_image, tuple(image_size.round_result()))
        self.scaled_alternate = pygame.transform.scale(
            self.alternate_image, tuple(image_size.round_result()))

    def Draw(self, surface, shift=Vector2D(0, 0), draw_end=None):
        if super().Draw(surface, shift, draw_end) == False:
            return False
        surface.blit(self.image, tuple(self.position + shift))

    def Update(self, shift=Vector2D(0, 0)):
        super().Update(shift)
        mouse_position = Vector2D(controls["mouse_position"]) - shift
        relative = mouse_position - self.position
        relative.y -= (self.padding.y + self.outline_size.y)
        if not (0 < relative.x < self.width and \
                0 < relative.y < self.unpadded_size.y):
            return
        if controls["mouse_pressed"][0]:
            current_pos = 0
            current_rating = 0
            add_image = False
            while current_pos < relative.x:
                if add_image:
                    current_pos += self.image_width
                    current_rating += 1
                    add_image = False
                else:
                    add_image = True
                    if current_rating == 0:
                        current_pos += self.outline_size.x + self.padding.x
                    else:
                        current_pos += self.padding.x
            if add_image == False and current_rating >= self.min_rating:  # i.e ended with mouse on an image
                self.rating = current_rating
                self.UpdateImage()
            elif add_image == True and current_rating <= self.min_rating:  # TODO check and test logic here
                # adds an option to set a minimum rating (generally 0)
                self.rating = self.min_rating
                self.UpdateImage()


class SearchBar(FunctionalEntry):
    def __init__(
            self,
            font,
            width,
            target,
            update_function,  # will be fed the text and cursor index,
            suggestion_use_function=None,
            max_suggestions=4,
            arguments=None,
            send_text=True,
            initial_key_time=0.4,
            key_time=0.04,
            padding=Vector2D(5, 5),
            outline_size=Vector2D(2, 2),
            initial_text="",
            empty_text="",
            hide_text=False,
            text_colour=(0, 0, 0),
            empty_text_colour=(140, 140, 140),
            background_colour=(200, 200, 200),
            search_background_colour=(200, 200, 200),
            suggestion_background_colour=(100, 100, 100),
            outline_colour=(0, 0, 0),
            history_range=500,
            tooltip_info=[None, 2],
            position=None,
            is_active=True,
            is_hidden=False):
        self.current_active_index = -1
        self.was_focused = False
        self.update_function = update_function
        self.suggestion_use_function = suggestion_use_function
        self.max_suggestions = max_suggestions
        self.search_background_colour = search_background_colour
        self.suggestion_background_colour = suggestion_background_colour
        self.suggestions = []
        self.suggestion_height = font.size(
            "ABCDEFGH")[1] + 2 * (outline_size.y + padding.y)
        self.background_size = self.suggestion_height * self.max_suggestions + outline_size.y
        super().__init__(font, width, target, arguments, send_text,
                         initial_key_time, key_time, padding, outline_size,
                         initial_text, empty_text, hide_text, text_colour,
                         empty_text_colour, background_colour, outline_colour,
                         history_range, tooltip_info, position, is_active,
                         is_hidden)

    def Reset(self):
        super().Reset()
        self.suggestions = []
        self.current_active_index = -1

    def UpdateImage(self):
        super().UpdateImage()
        self.standard_image = self.image
        image_size = Vector2D(self.standard_image.get_rect().size)
        new_size = image_size.copy()
        new_size.y += self.background_size
        self.focus_image = pygame.Surface(tuple(new_size), pygame.SRCALPHA, 32)
        self.focus_image.convert_alpha()
        self.focus_image.blit(self.standard_image, (0, 0))
        background_image = pygame.Surface((image_size.x, self.background_size),
                                          pygame.SRCALPHA, 32)
        background_image.convert_alpha()
        background_image.fill(self.search_background_colour)
        self.focus_image.blit(background_image, (0, image_size.y))

    def UseSuggestion(self, suggestion):
        if self.suggestion_use_function != None:
            self.suggestion_use_function(suggestion, self.text,
                                         self.cursor_index)

    def UpdateSuggestions(self, new_suggestions):
        self.current_active_index = -1
        num_of_suggestions = len(self.suggestions)
        if new_suggestions == None:
            return
        num_of_new = len(new_suggestions)
        pos = Vector2D(self.outline_size.x, self.height)
        for i in range(self.max_suggestions):
            if i > 0:
                pos.y += self.suggestions[i - 1].height
            if num_of_suggestions <= i:
                if num_of_new <= i:
                    text = ''
                    b_text = ''
                else:
                    text = new_suggestions[i]
                    b_text = text
                    while self.font.size(b_text +
                                         '...')[0] > self.max_text_width:
                        b_text = b_text[:-1]
                    if b_text != text:
                        b_text += '...'
                tooltip = Label(text, self.font, self.padding,
                                self.outline_size).image
                b = FixedHoverButton(
                    b_text,
                    self.font,
                    Vector2D(self.width - 2 * self.outline_size.x,
                             self.suggestion_height),
                    target=self.UseSuggestion,
                    arguments=text,
                    padding=self.padding,
                    background_colour=self.suggestion_background_colour,
                    outline_size=Vector2D(0, 0),
                    tooltip_info=[tooltip, 1],
                    position=pos.copy())
                if num_of_new <= i:
                    b.active = False
                self.suggestions.append(b)
            else:
                b = self.suggestions[i]
                if num_of_new <= i:
                    text = ''
                    b_text = ''
                else:
                    text = new_suggestions[i]
                    b_text = text
                if text == b.arguments:
                    if num_of_new <= i:
                        b.active = False
                    else:
                        b.active = True
                    continue
                if num_of_new > i:
                    while self.font.size(b_text +
                                         '...')[0] > self.max_text_width:
                        b_text = b_text[:-1]
                    if b_text != text:
                        b_text += '...'
                tooltip = Label(text, self.font, self.padding,
                                self.outline_size).image
                b.arguments = text
                b.text = b_text
                b.tooltip_image = tooltip
                b.UpdateImage()
                if num_of_new <= i:
                    b.active = False
                else:
                    b.active = True

    def UpdateActiveIndex(self):
        if self.current_active_index != -1:
            for i, s in enumerate(self.suggestions):
                if i < self.current_active_index and s.text == '':
                    self.current_active_index = i
                    self.UpdateActiveIndex()
                    return

    def DoKeyPress(self, name, unicode):
        if name == "up":
            self.current_active_index -= 1
            if self.current_active_index < -1:
                self.current_active_index = len(self.suggestions) - 1
            self.UpdateActiveIndex()
        elif name == "down":
            self.current_active_index += 1
            if self.current_active_index >= len(self.suggestions):
                self.current_active_index = -1
            self.UpdateActiveIndex()
        elif name == "escape":
            if self.current_active_index == -1:
                self.is_focused = False
            else:
                self.current_active_index = -1
            self.key_count += 1
            return
        super().DoKeyPress(name, unicode)

    def IsUnfocused(self):
        return not self.is_focused

    def Draw(self, surface, shift=Vector2D(0, 0), draw_end=None):
        if self.is_focused:
            self.image = self.focus_image
        else:
            self.image = self.standard_image
        if super().Draw(surface, shift, draw_end) == False:
            return False
        if not (self.is_focused and self.active):
            return
        for i, s in enumerate(self.suggestions):
            if self.current_active_index == -1:
                force_hover = None
            elif i == self.current_active_index:
                force_hover = True
            else:
                force_hover = False
            s.Draw(surface,
                   shift=(self.position + shift),
                   draw_end=draw_end,
                   force_hover=force_hover)

    def Update(self, shift=Vector2D(0, 0)):
        if self.active and self.is_focused:
            for s in self.suggestions:
                s.Update(shift=(self.position + shift), needs_release=False)
        prev_index = self.cursor_index

        if self.current_active_index == -1:
            if super().Update(shift, do_clear=False) == False:
                return False
        else:
            if Entry.Update(self, shift) == False:
                return False
            if self.is_focused:
                for event in controls["events"]:
                    if event.type == pygame.KEYDOWN and pygame.key.name(
                            event.key) == "return":
                        self.UseSuggestion(self.suggestions[
                            self.current_active_index].arguments)

        mouse_position = Vector2D(controls["mouse_position"]) - shift
        if controls.LeftClickDown and self.current_active_index != -1:
            relative_position = mouse_position - self.position
            self.is_focused = 0 < relative_position.x < self.width and \
                              0 < relative_position.y < self.height
            if self.is_focused:
                self.current_active_index = -1
        if self.cursor_index != prev_index:  # i.e. cursor index has changed
            new_suggestions = self.update_function(self.text,
                                                   self.cursor_index,
                                                   self.max_suggestions)
            if new_suggestions == None:
                self.UpdateSuggestions([])
            elif new_suggestions != [b.arguments for b in self.suggestions]:
                self.UpdateSuggestions(new_suggestions)
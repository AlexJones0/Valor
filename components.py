from interface import ScalePosition
from vectors import Vector2D
from controls import controls
from interface import BaseElement
import config
import pygame


class StaticComponent:
    def __init__(self,
                 position,
                 size,
                 background_colour,
                 ui_elements=None,
                 reset_func=None):
        if ui_elements == None:
            self.ui_elements = []
        else:
            self.ui_elements = ui_elements
        self.reset_func = reset_func
        self.position = position
        self.size = size
        self.width = self.size.x
        self.height = self.size.y
        self.background_colour = background_colour
        self.image = None
        self.cache_image = None
        self.UpdateImage()
        self.commands = []
        self.tab_list = []
        self.current_tab_index = 0

    def ResetTabIndex(self):
        self.current_tab_index = 0

    def ClearTabList(self):
        self.tab_list = []
        self.ResetTabIndex()

    def UpdateImage(self):
        self.image = pygame.Surface(tuple(self.size), pygame.SRCALPHA, 32)
        self.image.convert_alpha()
        self.image.fill(self.background_colour)

    def UpdateTabbedItem(self):
        if self.current_tab_index is None:
            return
        current = self.tab_list[self.current_tab_index]
        if hasattr(current, 'is_focused') and current.is_focused == True:
            current.is_focused = False
        self.current_tab_index += 1
        if self.current_tab_index == len(self.tab_list):
            self.current_tab_index = 0
        new = self.tab_list[self.current_tab_index]
        if hasattr(new, 'is_focused'):
            new.is_focused = True

    def UpdateTabIndex(self, prev_states):
        all_unfocused = True
        for item in prev_states.keys():
            if item.is_focused:
                all_unfocused = False
                if prev_states[item] == False:
                    for i, element in enumerate(self.tab_list):
                        if element == item:
                            self.current_tab_index = i
                            return
        if all_unfocused:
            self.current_tab_index = None

    @property
    def elements(self):
        return self.ui_elements

    def AddUIElement(self, ui_element):
        self.ui_elements.append(ui_element)

    def AddUIElements(self, *ui_elements):
        for element in ui_elements:
            self.AddUIElement(element)

    def RemoveUIElement(self, ui_element):
        self.ui_elements.remove(ui_element)

    def ClearUIElements(self):
        self.ui_elements = []

    def CreateCache(self):
        self.cache_image = self.image.copy()
        self.cache_image.convert_alpha()
        for element in self.ui_elements:
            element.Draw(self.cache_image)

    def DeleteCache(self):
        del self.cache_image
        self.cache_image = None

    def DrawCache(self, screen):
        screen.blit(self.cache_image, tuple(self.position))

    def Draw(self, screen, shift=Vector2D(0, 0), draw_end=None):
        screen.blit(self.image, tuple(self.position))
        for element in self.ui_elements:
            element.Draw(screen,
                         shift=(shift + self.position),
                         draw_end=draw_end)

    def AddCommand(self, command):
        self.commands.append(command)

    def AddCommands(self, *commands):
        for command in commands:
            self.AddCommand(command)

    def Update(self, shift=Vector2D(0, 0)):
        for event in controls["events"]:
            if event.type == pygame.KEYDOWN and pygame.key.name(
                    event.key) == "tab":
                self.UpdateTabbedItem()
                break
        prev_tabs = {}
        for element in self.tab_list:
            if hasattr(element, 'is_focused'):
                prev_tabs[element] = element.is_focused
        for element in self.ui_elements:
            element.Update(shift=(shift + self.position))
        self.UpdateTabIndex(prev_tabs)
        to_return = [c for c in self.commands]
        self.commands = [
        ]  # clear at the end to allow commands to be added to this component from other component's updates (e.g.
        # they call a function that interacts with this component's elements which in turn add a command)
        return to_return


class ScrollComponent(StaticComponent):
    def __init__(self,
                 position,
                 size,
                 max_height,
                 background_colour,
                 ui_elements=None,
                 reset_func=None,
                 automate_max_height=True,
                 automate_max_scroll=False):
        super().__init__(position, size, background_colour, ui_elements,
                         reset_func)
        self.max_height = max_height
        self.max_scroll = max_height - self.height
        self.current_scroll = 0
        self.scroll_speed = 25
        self.automate_max_height = automate_max_height
        self.automate_max_scroll = automate_max_scroll
        self.additional_height = config.settings["screen_height"] // 200
        self.updated_upon_exit = False  # flag to update all elements once
        # when the mouse stops hovering over the component to avoid lingering
        # tooltips, hover backgrounds etc.

    def AddUIElement(self, ui_element):
        super().AddUIElement(ui_element)
        # done seperately here to self.UpdateMaxHeight for efficiency - it is much
        # more efficient to only check the 1 added element then every single element again.
        if self.automate_max_height:
            height = ui_element.position.y + ui_element.height
            if height > (self.max_height - self.additional_height):
                self.max_height = height + self.additional_height
                self.max_scroll = self.max_height - self.height
        if self.automate_max_scroll:
            self.current_scroll = self.max_scroll

    def ClearUIElements(self):
        super().ClearUIElements()
        if self.automate_max_height:
            self.max_height = self.height
            self.max_scroll = 0
            self.current_scroll = 0

    def UpdateMaxHeight(self):
        if len(self.ui_elements) == 0:
            return
        greatest_height = self.ui_elements[0].position.y + self.elements[
            0].height
        for e in self.ui_elements:
            height = e.position.y + e.height
            if height > greatest_height:
                greatest_height = height
        if greatest_height > (self.max_height - self.additional_height):
            self.max_height = height + self.additional_height
        elif greatest_height < (self.max_height - self.additional_height):
            self.max_height = greatest_height + self.additional_height
        if greatest_height < (self.height - self.additional_height):
            self.max_height = self.height
        self.max_scroll = self.max_height - self.height
        if self.current_scroll > self.max_scroll:
            self.current_scroll = self.max_scroll

    def RemoveUIElement(self, ui_element):
        super().RemoveUIElement(ui_element)
        if self.automate_max_height:
            self.UpdateMaxHeight()

    def CreateCache(self):
        self.cache_image = self.image.copy()
        self.cache_image.convert_alpha()
        coord1 = Vector2D(0, self.current_scroll)
        coord2 = Vector2D(self.width, self.current_scroll + self.height)
        for element in self.ui_elements:
            if element.WithinBoundingBox(coord1, coord2):
                element.Draw(self.cache_image,
                             shift=Vector2D(0, -self.current_scroll))

    def Draw(self, screen, shift=Vector2D(0, 0), draw_end=None):
        screen.blit(self.image, tuple(self.position))
        image = pygame.Surface(tuple(self.size), pygame.SRCALPHA, 32)
        image.convert_alpha()
        coord1 = Vector2D(0, self.current_scroll)
        coord2 = Vector2D(self.width, self.current_scroll + self.height)
        for element in self.ui_elements:
            if element.WithinBoundingBox(coord1, coord2):
                element.Draw(image,
                             shift=Vector2D(0, -self.current_scroll),
                             draw_end=draw_end)
        screen.blit(image, tuple(self.position + shift))

    def Update(self, shift=Vector2D(0, 0)):
        for event in controls["events"]:
            if event.type == pygame.KEYDOWN and pygame.key.name(
                    event.key) == "tab":
                self.UpdateTabbedItem()
                break
        prev_tabs = {}
        for element in self.tab_list:
            if hasattr(element, 'is_focused'):
                prev_tabs[element] = element.is_focused
        mouse_position = Vector2D(
            controls["mouse_position"]) - self.position - shift
        change = shift + self.position
        change.y -= self.current_scroll
        if 0 < mouse_position.x < self.width and 0 < mouse_position.y < self.height:
            self.updated_upon_exit = False
            for event in controls["events"]:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 5:  #scroll down
                        if self.current_scroll < self.max_scroll:
                            self.current_scroll += self.scroll_speed
                            if self.current_scroll > self.max_scroll:
                                self.current_scroll = self.max_scroll
                    elif event.button == 4:  #scroll up
                        if self.current_scroll > 0:
                            self.current_scroll -= self.scroll_speed
                            if self.current_scroll < 0:
                                self.current_scroll = 0
            for element in self.ui_elements:
                if element.WithinBoundingBox(
                        Vector2D(0, self.current_scroll),
                        Vector2D(self.width,
                                 self.current_scroll + self.height)):
                    element.Update(shift=change)
            #for element in self.ui_elements:  TODO: might break something, not sure, so leaving commented for now rather than deleting
            #    element.active = True
        elif not self.updated_upon_exit:
            for element in self.ui_elements:
                element.Update(shift=change)
            self.updated_upon_exit = True
        self.UpdateTabIndex(prev_tabs)
        to_return = [c for c in self.commands]
        self.commands = [
        ]  # clear at the end to allow commands to be added to this component from other component's updates (e.g.
        # they call a function that interacts with this component's elements which in turn add a command)
        return to_return


class MultiComponent:
    def __init__(self, components=None):
        if components == None:
            self.components = []
        else:
            self.components = components
        self.commands = []
        self.position = Vector2D(0, 0)
        self.size = Vector2D(0, 0)
        self.width = 0
        self.height = 0
        self.UpdateSize()
        self.reset_func = self.Reset

    def Reset(self):
        for component in self.components:
            if component.reset_func is not None:
                component.reset_func()

    @property
    def elements(self):
        all_elements = []
        for component in self.components:
            all_elements += component.elements
        return all_elements

    def AddComponent(self, component):
        self.components.append(component)
        self.UpdateSize()

    def AddComponents(self, *components):
        for component in components:
            self.AddComponent(component)

    def RemoveComponent(self, component):
        self.components.remove(component)
        self.UpdateSize()

    def ClearComponents(self):
        self.components = []
        self.UpdateSize()

    def UpdateSize(self):
        if len(self.components) == 0:
            self.size = Vector2D(0, 0)
            self.width = 0
            self.height = 0
        lowest = self.components[0].position.copy()
        highest = self.components[0].position + self.components[0].size
        for component in self.components[1:]:
            if component.position.x < lowest.x:
                lowest.x = component.position.x
            if component.position.y < lowest.y:
                lowest.y = component.position.y
            upper_pos = component.position + component.size
            if upper_pos.x > highest.x:
                highest.x = upper_pos.x
            if upper_pos.y > highest.y:
                highest.y = upper_pos.y
        self.size = highest - lowest
        self.width = self.size.x
        self.height = self.size.y

    def CreateCache(self):
        for component in self.components:
            component.CreateCache()
        self.cache_image = pygame.Surface(tuple(self.size), pygame.SRCALPHA,
                                          32)
        self.cache_image.convert_alpha()
        for component in self.components:
            if component.cache_image == None:
                component.CreateCache()
            self.cache_image.blit(component.cache_image,
                                  tuple(component.position))

    def DeleteCache(self):
        del self.cache_image
        self.cache_image = None
        for component in self.components:
            component.DeleteCache()

    def DrawCache(self, screen):
        screen.blit(self.cache_image, tuple(self.position))

    def Draw(self, screen, shift=Vector2D(0, 0)):
        for component in self.components:
            component.Draw(screen, shift=(shift + self.position))

    def AddCommand(self, command):
        self.commands.append(command)

    def AddCommands(self, *commands):
        for command in commands:
            self.AddCommand(command)

    def Update(self):
        for component in self.components:
            self.commands += component.Update()
        to_return = [c for c in self.commands]
        self.commands = [
        ]  # clear at the end to allow commands to be added to this component from other component's updates (e.g.
        # they call a function that interacts with this component's elements which in turn add a command)
        return to_return
import pygame
import config
import debug
from glob import glob as FileTraverse
from controls import controls
from data_types import Queue
import SQL
from vectors import Vector2D
import transitions
import json
from threading import Thread
import encryption

global events
events = Queue()


class ScreenComponent:
    """ This class stores something that can be drawn to the screen / interacted with on screen and allows multiple
        visual components to be managed in the same loop. """
    def __init__(self,
                 component,
                 drawScreen,
                 id_,
                 active=True,
                 visuals_active=True):
        """" Initialises the ScreenComponent Object. """
        self.component = component
        self.draw_screen = drawScreen
        self.active = active
        self.state = "NORMAL"
        self.visuals_active = visuals_active
        self.id_ = id_

    @property
    def elements(self):
        return self.component.elements

    @property
    def position(self):
        return self.component.position

    @position.setter
    def position(self, new_position):
        self.component.position = new_position

    def UpdateSize(self, new_size):
        self.component.UpdateSize(new_size)

    def Leave(self):
        self.active = False
        self.visuals_active = False

    def Reset(self):
        if self.component.reset_func != None:
            self.component.reset_func()

    def Join(self):
        self.Reset()
        # TODO check not sure if needed
        #if self.component.cache_image != None:
        #    self.component.DeleteCache()
        #    self.state = "NORMAL"
        self.active = True
        self.visuals_active = True

    def DeactivateAndCache(self):
        self.component.CreateCache()
        self.active = False
        self.state = "INACTIVE"

    def Activate(self):
        self.component.DeleteCache()
        self.active = True
        self.state = "NORMAL"

    def StartTransitioning(self):
        self.component.CreateCache()
        self.state = "TRANSITIONING"

    def StopTransitioning(self):
        self.component.DeleteCache()
        self.state = "NORMAL"

    def Update(self):
        """ Updates the related component if active. """
        if self.active and self.state != "TRANSITIONING":
            return self.component.Update()

    def Draw(self, draw_end=None):
        """ Draws the related component if visuals are active. """
        if self.visuals_active:
            if self.state in ["TRANSITIONING", "INACTIVE"]:
                self.component.DrawCache(self.draw_screen)
            else:
                self.component.Draw(self.draw_screen, draw_end=draw_end)


class MainLoop:
    """ This class stores information about the program and runs its main loop. """
    def __init__(self):
        """ Initialises the main program loop; handles interfacing with pygame on a low level.
              Inputs: None
              Outputs: None"""
        pygame.init()
        pygame.font.init()
        if "logs" not in FileTraverse("*"):
            from os import mkdir as MakeFileDir
            MakeFileDir("logs")
        debug.CreateLogFile("logs\\")
        debug.Log("Started logging.")
        self.__LoadConfig()
        self.UpdateWindow()
        self.__clock = pygame.time.Clock()
        controls["mouse_pressed"] = []
        controls["control_events"] = []
        controls["keys_pressed"] = []
        controls["mouse_position"] = []
        self.__components = []
        self.transitions_controller = transitions.TransitionObject()
        self.background_images = None
        self.using_background_image = False
        self.current_bg_index = 0
        transitions.CreateMenuTransitions()

    def __LoadBackgroundImage(self):
        if config.settings["background_image"] == None:
            return
        try:
            if isinstance(config.settings["background_image"], str):
                background_images = [config.settings["background_image"]]
            else:  # a list
                background_images = config.settings["background_image"]
            self.background_images = []
            for image in background_images:
                if image.endswith(".txt"):
                    from base64 import decodebytes as B64DecodeBytes
                    with open(image, 'rb') as f:
                        image_data = B64DecodeBytes(
                            str.encode(encryption.DecryptText(
                                config.settings["key"], f.read()),
                                       encoding='ASCII'))
                        f.close()
                    with open('gui\\images\\background_temp.png', 'wb+') as f:
                        f.write(image_data)
                        f.seek(0)
                        image = pygame.image.load(f)
                        f.close()
                    with open('gui\\images\\background_temp.png', 'wb+') as f:
                        f.truncate(0)
                        f.close()
                else:
                    image = pygame.image.load(image)
                image = pygame.transform.scale(
                    image, tuple(config.settings["window_size"]))
                image.convert_alpha()
                self.background_images.append(image)
            self.using_background_image = True
            debug.Log("Loaded background image to use as background.")
        except Exception as e:
            debug.Log(f'Failure to load background image. Reason: {e}')

    def __LoadConfig(self):
        config.ReadConfig()
        config.settings["window_size"] = Vector2D(
            config.settings["window_width"], config.settings["window_height"])
        display_info_obj = pygame.display.Info()
        config.settings["screen_width"] = display_info_obj.current_w
        config.settings["screen_height"] = display_info_obj.current_h
        config.settings["screen_size"] = Vector2D(
            config.settings["screen_width"], config.settings["screen_height"])
        if config.settings["display_mode"] == '':
            config.settings["display_mode"] = 'windowed'
        config.settings["background_colour"] = (255, 255, 255)

    def __UpdateFullscreenWindowSize(self):
        """ Updates the 'window_width' and 'window_height' settings in the settings dictionary to
            their respective fullscreen values (if needed).
              Inputs: None
              Outputs: None"""
        screenWidth = config.settings["screen_width"]
        if config.settings["window_width"] != screenWidth:
            config.settings["window_width"] = screenWidth
        screenHeight = config.settings["screen_height"]
        if config.settings["window_height"] != screenHeight:
            config.settings["window_height"] = screenHeight
        config.settings["window_size"] = Vector2D(
            config.settings["window_width"], config.settings["window_height"])

    def UpdateWindow(self):
        """ Updates the pygame window based upon saved settings. Changes the size, mode and caption of the window
            and handles pygame display related arguments."""
        if config.settings["display_mode"] == "fullscreen":
            self.__UpdateFullscreenWindowSize()
            displayArgs = pygame.FULLSCREEN | pygame.HWSURFACE | pygame.DOUBLEBUF  # | denotes bitwise-OR
            self.__doUpdateWindow = False
        elif config.settings["display_mode"] in [
                "windowed borderless", "borderless windowed",
                "fullscreen borderless", "borderless fullscreen"
        ]:
            self.__UpdateFullscreenWindowSize()
            from os import environ
            environ['SDL_VIDEO_WINDOW_POS'] = '0, 0'
            displayArgs = pygame.NOFRAME
            self.__doUpdateWindow = False
        else:  # windowed mode
            from os import environ
            environ['SDL_VIDEO_WINDOW_POS'] = '0, 30'
            displayArgs = ''
            self.__doUpdateWindow = True
        if displayArgs == '':
            self.screen = pygame.display.set_mode(
                (config.settings["window_width"],
                 config.settings["window_height"]))
        else:
            self.screen = pygame.display.set_mode(
                (config.settings["window_width"],
                 config.settings["window_height"]), displayArgs)
        pygame.display.set_caption('Project Valor')
        pygame.display.set_icon(pygame.image.load('gui\\images\\Logo32.png'))

    def __UpdateControls(self):
        """ Updates the controls object based upon input controls retrieved from pygame. """
        controls["mouse_pressed"] = pygame.mouse.get_pressed()
        controls["events"] = pygame.event.get()
        controls["keys_pressed"] = pygame.key.get_pressed()
        controls["mouse_position"] = pygame.mouse.get_pos()

    def AddComponent(self, component, id_, active=True, visuals_active=True):
        """ Adds an input component to the main loop's list of components to manage. Returns a reference
            to the new created ScreenComponent object. """
        new_component = ScreenComponent(component,
                                        self.screen,
                                        id_,
                                        active=active,
                                        visuals_active=visuals_active)
        self.__components.append(new_component)
        self.__components = sorted(self.__components, key=lambda k: k.id_)
        return new_component

    def RemoveComponent(self, component):
        """ Removes an input component from the main loop's list of components to manage.
            Returns True if successful otherwise returns False"""
        try:
            self.__components.remove(component)
            return True
        except:
            return False

    def ClearComponents(self):
        """ Completely clears the main loop's list of components to manage. """
        self.__components = []

    def FindComponent(self, id_):
        for component in self.__components:
            if component.id_ == id_:
                return component
            elif component.id_ > id_:
                return False  # components are stored in id order so if passed, not found
        return False

    def SetComponentActiveState(self, id_, state):
        if isinstance(id_, ScreenComponent):
            component = id_
        else:
            component = self.FindComponent(id_)
        if component != False:
            component.active = state

    def SetComponentVisualsState(self, id_, state):
        if isinstance(id_, ScreenComponent):
            component = id_
        else:
            component = self.FindComponent(id_)
        if component != False:
            component.visuals_active = state

    def HandleTransitionCommand(self, command):
        transitions_to_add = command["TRANSITIONS"]
        for transition in transitions_to_add:
            post_args = []
            elements = transition["ELEMENTS"]
            if not isinstance(elements, list):
                elements = [elements]
            for i in range(len(elements)):
                element = elements[i]
                if isinstance(element, int):
                    elements[i] = self.FindComponent(element)
                    if transition["TYPE"] == "JOINING":
                        elements[i].Reset(
                        )  # we must reset before we start transitioning
                        # or the cached image used during the transition will be of the
                        # not-reset menu.
                    elements[i].StartTransitioning()
                    post_args.append({
                        "TYPE": "EXECUTE",
                        "FUNCTION": elements[i].StopTransitioning,
                        "ARGUMENTS": [],
                        "KWARGUMENTS": {}
                    })

            transition_style = transitions.menu_transitions[
                transition["STYLE"]]
            # TODO IMPROVE COMPATABILITY WITH ELEMENTS (NOT COMPONENTS) BEING CHANGED IN POST ARGUMENTS. RIGHT NOW ONLY WORKS FOR COMPONENTS
            if transition["TYPE"] == "JOINING":
                for element in elements:
                    if isinstance(element, ScreenComponent):
                        element.position = transition_style[0].copy()
                        # we don't reset here, see above.
                        element.active = True
                        element.visuals_active = True
            elif transition["TYPE"] == "LEAVING":
                for element in elements:
                    if isinstance(element, ScreenComponent):
                        post_args.append({"TYPE": "LEAVE", "ID": element.id_})
            if "POST_ARGS" in transition.keys():
                post_args += transition["POST_ARGS"]
            movement_vector = transition_style[1]
            if "MOVEMENT_VECTOR" in transition.keys():
                movement_vector = transition["MOVEMENT_VECTOR"]
            transition = transitions.TransitionRequest(
                elements,
                movement_vector,
                transition_style[2],
                transition_style[3],
                transition["TIME"] / config.settings["transition_speed"],
                transition["DELAY"] / config.settings["transition_speed"],
                post_args=post_args)
            self.transitions_controller.AddTransition(transition)
            del transition

    def HandleCommandExecution(self, function, data, *args, **kwargs):
        if isinstance(data, list):
            results = []
            for i in data:
                results.append(function(i, *args, **kwargs))
            return results
        else:
            return function(data, *args, **kwargs)

    def HandleCommand(self, command):
        if command["TYPE"] == "TRANSITION":
            self.HandleTransitionCommand(command)
        elif command["TYPE"] == "ACTIVATE":
            components = self.HandleCommandExecution(self.FindComponent,
                                                     command["ID"])
            self.HandleCommandExecution(ScreenComponent.Activate, components)
        elif command["TYPE"] == "DEACTIVATE":
            components = self.HandleCommandExecution(self.FindComponent,
                                                     command["ID"])
            if "CACHE" in command and command["CACHE"] == True:
                self.HandleCommandExecution(ScreenComponent.DeactivateAndCache,
                                            components)
            else:
                self.HandleCommandExecution(self.SetComponentActiveState,
                                            components, False)
        elif command["TYPE"] == "SHOW":
            self.HandleCommandExecution(self.SetComponentVisualsState,
                                        command["ID"], True)
        elif command["TYPE"] == "HIDE":
            self.HandleCommandExecution(self.SetComponentVisualsState,
                                        command["ID"], False)
        elif command["TYPE"] == "LEAVE":
            components = self.HandleCommandExecution(self.FindComponent,
                                                     command["ID"])
            self.HandleCommandExecution(ScreenComponent.Leave, components)
        elif command["TYPE"] == "JOIN":
            components = self.HandleCommandExecution(self.FindComponent,
                                                     command["ID"])
            self.HandleCommandExecution(ScreenComponent.Join, components)
        elif command["TYPE"] == "RESET":
            components = self.HandleCommandExecution(self.FindComponent,
                                                     command["ID"])
            self.HandleCommandExecution(ScreenComponent.Reset, components)
        elif command["TYPE"] == "EXECUTE":
            if "THREADED" in command and command["THREADED"]:
                Thread(target=command["FUNCTION"],
                       args=command["ARGUMENTS"],
                       kwargs=command["KWARGUMENTS"],
                       daemon=True).start()
            else:
                command["FUNCTION"](*command["ARGUMENTS"],
                                    **command["KWARGUMENTS"])
        elif command[
                "TYPE"] == "MOVE":  # not updated to take multiple component ids
            self.FindComponent(
                command["ID"]).position = command["POSITION"].copy()
        elif command[
                "TYPE"] == "STATE":  # not updated to take multiple component ids
            self.FindComponent(command["ID"]).state = command["STATE"]
        elif command["TYPE"] == "UPDATE BACKGROUND":
            self.__LoadBackgroundImage()

    def __Update(self):
        """ Updates the program for a frame, ticking the clock, drawing to the screen, updating
            components and checking for quit conditions. """
        self.__clock.tick(config.settings["fps_limit"])
        self.screen.fill(config.settings["background_colour"])
        self.__UpdateControls()
        if self.using_background_image:
            image = self.background_images[self.current_bg_index]
            self.screen.blit(image, (0, 0))
            for event in controls["events"]:
                if event.type == pygame.KEYDOWN:
                    key = pygame.key.name(event.key)
                    if key == "f5":
                        self.current_bg_index += 1
                        if self.current_bg_index == len(
                                self.background_images):
                            self.current_bg_index = 0

        #controls.PrintIndexOfDown()  #  TODO REMOVE
        #controls.PrintNameOfKeyDown()  #  TODO REMOVE
        #for component in self.__components:  # TODO REMOVE
        #    if component.visuals_active:  # TODO REMOVE
        #        print(str(component.id_) + "-" + str(component.position),
        #              end=',')  # TODO REMOVE
        #print()  # TODO REMOVE

        for command in self.transitions_controller.Update():
            self.HandleCommand(command)

        #print([(str(i.id_) + " " + str(i.active) + " " + i.state)
        #       for i in self.__components])
        draw_end = []
        for component in self.__components:
            result = component.Update()
            if result != None:
                for command in result:
                    if command["TYPE"] == "STOP":
                        debug.Log(
                            "Execution stopped normally as a result of an 'exit' command being issued."
                        )
                        return False
                    self.HandleCommand(command)
            component.Draw(draw_end=draw_end)
        for item in draw_end:
            self.screen.blit(*item)

        for event in controls["events"]:
            if event.type == pygame.QUIT:
                debug.Log("User manually quit by closing the window.")
                return False

        # TODO temp to remove - just lets you exit the game by pressing escape and shift simultaneously
        if controls["keys_pressed"][304] and \
            controls["keys_pressed"][27]:
            debug.Log("User manually quit using shift-escape combination.")
            return False

        pygame.display.flip()
        return True

    def Start(self):
        """ Starts the main loop of the program, continually running the update loop until
            it returns false. """
        while self.__Update():
            continue
        debug.Log("Execution finished as expected on quit.")


if __name__ == "__main__":
    testMainObject = MainLoop()
    testMainObject.Start()

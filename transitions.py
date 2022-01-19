from time import time as CurrentTime
from vectors import Vector2D
import config
from math import sin, cos, pi


def EaseLinear(start, end, percent):
    return start + (end - start) * percent


def EaseOutQuadratic(start, end, percent):
    return start + (end - start) * -(percent * (percent - 2))


def EaseInQuadratic(start, end, percent):
    return start + (end - start) * percent * percent


def EaseInOutQuadratic(start, end, percent):
    if percent <= 0.5:
        return EaseInQuadratic(start, (start + end) / 2, percent * 2)
    else:
        return EaseOutQuadratic((start + end) / 2, end, percent * 2 - 1)


def EaseGeneralQuadratic(a, b, start, end, percent):
    # The only rule is that f(0) = 0 and f(1) = 1 (i.e. a + b = 1)
    return start + (end - start) * (a * percent * percent + b * percent)


def EaseInOutCubic(start, end, percent):
    if percent <= 0.5:
        return start + (end - start) * 4 * percent * percent * percent
    else:
        return start + (end - start) * (0.5 * (2 * percent - 2) *
                                        (2 * percent - 2) *
                                        (2 * percent - 2) + 1)


def EaseOutBounce(start, end, percent):
    if percent < 4 / 11:
        multiplier = 121 * percent * percent / 16
    elif percent < 8 / 11:
        multiplier = 9.075 * percent * percent - 9.9 * percent + 3.4
    elif percent < 0.9:
        multiplier = 4356 / 361 * percent * percent - 35442 / 1805 * percent + 16061 / 1805
    else:
        multiplier = 10.8 * percent * percent - 20.52 * percent + 10.72
    return start + (end - start) * multiplier


def EaseInBounce(start, end, percent):
    return 1 - EaseOutBounce(0, 1, 1 - percent)


def DoNothing(start, end, percent):
    return end


class TransitionRequest:
    def __init__(self,
                 elements,
                 movement_vector,
                 transition_type,
                 transition_args,
                 transition_time,
                 transition_delay,
                 post_args=None):
        self.elements = elements
        self.movement_vector = movement_vector
        self.transition_func = transition_type
        self.transition_args = transition_args
        self.transition_time = transition_time
        self.delay = transition_delay
        self.start_positions = [
            e[1] if isinstance(e, tuple) else e.position for e in elements
        ]  # store start positions in case 1. they are needed or 2. linear function transitions
        self.time_of_start = 0
        self.post_args = post_args
        self.moved = Vector2D(0, 0)


class TransitionObject:
    def __init__(self, transitions=None):
        # each transition follows the format [elements, movement_vector, type, arguments, time, delay]
        # the final 2 indexes are added on by the code and are just a copy of the start positions and the time the transition started
        self.start_positions = []
        if transitions == None:
            self.transitions = []
        self.prev_time = 0
        self.time = 0

    def AddTransition(self, transition):
        self.transitions.append(transition)

    def Update(self):
        if len(self.transitions) == 0:
            return []
        self.prev_time = self.time
        self.time = CurrentTime()
        to_remove = []
        elements = {}
        # store all elements, calculate change vectors per element and add them at the end.
        # allows for multiple simultaneous transitions to affect the same element.
        # update the start position of later transitions to the end result of any earlier transition to resolve start position complaints.
        for t in self.transitions:
            for e in t.elements:
                if e not in elements:
                    elements[e] = Vector2D(0, 0)
        post_args = []
        for t in self.transitions:
            if t.time_of_start == 0:
                t.time_of_start = self.time
            percent = (self.time - t.time_of_start -
                       t.delay) / t.transition_time
            prev_percent = (self.prev_time - t.time_of_start -
                            t.delay) / t.transition_time
            if percent >= 1:
                percent = 1
                post_args += t.post_args
                to_remove.append(t)
                # change_vector to account for minute floating point errors etc.
                # calculated to take exact end position
                if isinstance(t.movement_vector, Vector2D):
                    change_vector = t.movement_vector - t.moved
                else:
                    change_vector = t.movement_vector
            elif percent <= 0:  # to account for added delay
                continue
            else:
                if prev_percent < 0:
                    prev_percent = 0
                if t.transition_args != None:
                    if not isinstance(t.movement_vector, Vector2D):
                        change_vector = t.transition_func(
                            *t.transition_args, 0, t.movement_vector, percent)
                    else:
                        change_vector = Vector2D(
                            t.transition_func(*t.transition_args, 0,
                                              t.movement_vector.x, percent) -
                            t.transition_func(*t.transition_args, 0,
                                              t.movement_vector.x,
                                              prev_percent),
                            t.transition_func(*t.transition_args, 0,
                                              t.movement_vector.y, percent) -
                            t.transition_func(*t.transition_args, 0,
                                              t.movement_vector.y,
                                              prev_percent))
                elif not isinstance(t.movement_vector, Vector2D):
                    change_vector = t.transition_func(0, t.movement_vector,
                                                      percent)
                else:
                    change_vector = Vector2D(
                        t.transition_func(0, t.movement_vector.x, percent) -
                        t.transition_func(0, t.movement_vector.x,
                                          prev_percent),
                        t.transition_func(0, t.movement_vector.y, percent) -
                        t.transition_func(0, t.movement_vector.y,
                                          prev_percent))
            for i in range(len(t.elements)):
                if isinstance(t.elements[i], tuple):
                    t.elements[i][0](t.start_positions[i] + change_vector)
                    continue
                elements[t.elements[i]] += change_vector
            if isinstance(change_vector, Vector2D):
                t.moved += change_vector
        for e in elements.keys():
            if not isinstance(e, tuple):
                e.position += elements[e]
        for t in to_remove:
            self.transitions.remove(t)
        del to_remove
        return post_args


global menu_transitions
menu_transitions = {
}  # format is id: joining_pos, position_change, transition type, transition arguments


def CreateMenuTransitions():
    global menu_transitions
    menu_transitions[1] = [
        Vector2D(0, config.settings["window_height"]),
        Vector2D(0, -config.settings["window_height"]), EaseInOutCubic, None
    ]  # Vertical Upwards Swipe
    menu_transitions[2] = [
        Vector2D(0, -config.settings["window_height"]),
        Vector2D(0, config.settings["window_height"]), EaseInOutCubic, None
    ]  # Vertical Downwards Swipe
    menu_transitions[3] = [
        Vector2D(0, 2 * config.settings["window_height"]),
        Vector2D(0, -2 * config.settings["window_height"]), EaseInOutCubic,
        None
    ]  # Vertical Upwards Swipe With Gap
    menu_transitions[4] = [
        Vector2D(0, -2 * config.settings["window_height"]),
        Vector2D(0, 2 * config.settings["window_height"]), EaseInOutCubic, None
    ]  # Vertical Downwards Swipe With Gap
    menu_transitions[5] = [0, 224, EaseInOutCubic,
                           None]  # Alpha Fade to darken background (7/8)
    menu_transitions[6] = [
        Vector2D(config.settings["window_width"], 0),
        Vector2D(-(config.settings["window_width"] / 2), 0), EaseInOutCubic,
        None
    ]  # Horizontal Left Half Swipe
    menu_transitions[7] = [
        Vector2D(0, -(config.settings["window_height"] / 7)),
        Vector2D(0, config.settings["window_height"] / 7), EaseOutQuadratic,
        None
    ]  # 1/7 Bar Movement Vertically Down From Top
    menu_transitions[8] = [224, -224, EaseInQuadratic,
                           None]  # Alpha Fade to lighten background (7/8)
    menu_transitions[9] = [
        Vector2D(config.settings["window_width"] / 2, 0),
        Vector2D(config.settings["window_width"] / 2, 0), EaseInOutCubic, None
    ]  # Horizontal Right Half Swipe
    menu_transitions[10] = [
        Vector2D(0, config.settings["window_width"] / 7),
        Vector2D(0, -(config.settings["window_width"] / 7)), EaseInOutCubic,
        None
    ]  # 1/7 Bar Movement Vertically Up To Top
    menu_transitions[11] = [
        Vector2D(0, -(config.settings["window_width"] / 7)),
        Vector2D(0, config.settings["window_width"] / 7), EaseOutBounce, None
    ]  # 1/7 Bar Movement Vertically Down From Top; Bouncy
    menu_transitions[12] = [
        Vector2D(config.settings["window_width"] * 1.025,
                 config.settings["window_height"] * (0.45 + 1 / 60)),
        Vector2D(-(config.settings["window_width"] / 2), 0), EaseInOutCubic,
        None
    ]  # Horizontal Left Half Swipe from partway down
    menu_transitions[13] = [
        Vector2D(config.settings["window_width"] * 1.275,
                 config.settings["window_height"] * 7 / 120),
        Vector2D(-(config.settings["window_width"] / 2), 0), EaseInOutCubic,
        None
    ]  # Horizontal Left Half Swipe from right side
    menu_transitions[14] = [
        Vector2D(0, -config.settings["window_height"]),
        Vector2D(0, config.settings["window_height"]), EaseInQuadratic, None
    ]  # Vertical Downwards Swipe (Quadratic, ease in)
    menu_transitions[15] = [
        Vector2D(0, -config.settings["window_height"]),
        Vector2D(0, config.settings["window_height"]), EaseOutQuadratic, None
    ]  # Vertical Downwards Swipe (Quadratic, ease out)
    menu_transitions[16] = [
        Vector2D(0, 0),
        Vector2D(0, -config.settings["window_height"] * 11 / 180),
        EaseInOutCubic, None
    ]  # Vertical Upwards Movement (1/18)
    menu_transitions[17] = [
        Vector2D(0, 0), Vector2D(0, 0), DoNothing, None
    ]  # Does nothing, used as a delay timer to activate post transition arguments
    menu_transitions[18] = [
        Vector2D(0, 0), Vector2D(0, 0), EaseInOutCubic, None
    ]  # Generic EaseInOutCubic Transition (may remove later when more functionality is added TODO)
    menu_transitions[19] = [
        Vector2D(config.settings["window_width"], 0),
        Vector2D(-config.settings["window_width"], 0), EaseInOutCubic, None
    ]  # Sidebar move in from right side of the screen
    menu_transitions[20] = [
        Vector2D(0, 0),
        Vector2D(-config.settings["window_width"], 0), EaseInOutCubic, None
    ]  # Sidebar move out of left side of the screen
    menu_transitions[21] = [
        Vector2D(-config.settings["window_width"], 0),
        Vector2D(config.settings["window_width"], 0), EaseInOutCubic, None
    ]  # Swipe from bottom up 6/7ths of the screen
    menu_transitions[22] = [
        Vector2D(config.settings["window_width"] * 0.3554237565,
                 -config.settings["window_height"] * 0.5158115183246),
        Vector2D(0, config.settings["window_height"]), EaseInOutCubic, None
    ]  # item tags list swipes down from top of scren
    menu_transitions[23] = [
        Vector2D(config.settings["window_width"] * 0.3554237565,
                 config.settings["window_height"] * 1.4841884816754),
        Vector2D(0, -config.settings["window_height"]), EaseInOutCubic, None
    ]  # item tags list swipes in upwards from bottom of scren
    menu_transitions[24] = [
        Vector2D(config.settings["window_width"], 0),
        Vector2D(-config.settings["window_width"], 0), EaseInOutCubic, None
    ]  # Horizontal swipe left
    menu_transitions[25] = [
        Vector2D(-config.settings["window_width"], 0),
        Vector2D(config.settings["window_width"], 0), EaseInOutCubic, None
    ]  # Horizontal swipe right


if __name__ == "__main__":
    for i in range(100):
        percent = i / 100
        print(EaseInOutCubic(0, 1000, percent))
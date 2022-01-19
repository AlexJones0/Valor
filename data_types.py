class Stack:
    """ A variable-length LIFO data structure where each item is added to the
        top of the stack."""

    def __init__(self, *args):
        """ The constructor for a stack.
              Inputs: Takes any number of any items to put in the stack.
              Outputs: None."""
        self.items = [*args]

    @property
    def is_empty(self):
        """ A property that returns a Boolean value detailing whether the stack
            is empty (it has no items)."""
        return len(self.items) == 0

    def __len__(self):
        """ A method that returns the length of the stack (an integer)."""
        return self.items.__len__()

    def push(self, item):
        """ This method pushes a new item to the top of the stack, so that it
            will be the last item in.
              Inputs: item (any object that is to be pushed to the stack).
              Outputs: None."""
        self.items.append(item)

    def pop(self):
        """ This method pops an item from the stack, removing it from the stack
            and returning it.
              Inputs: None.
              Outputs: The item that was currently occupying the last (top)
            space in the stack."""
        if len(self.items) == 0:
            return None
        else:
            last_item = self.items[-1]
            self.items = self.items[:-1]
            return last_item

    def remove(self):
        """ This method removes an item from the top of the stack, removing it
            from the stack and not returning it.
              Inputs: None.
              Outputs: None."""
        if len(self.items) != 0:
            self.items = self.items[:-1]

    def peek(self):
        """ This method peeks at the top item of the stack, returning it but not
            removing it from the stack.
              Inputs: None.
              Outputs: The item that was currently occupying the last (top)
            space in the stack."""
        if len(self.items) > 0:
            return self.items[-1]
        else:
            return None

    def clear(self):
        """ This method completely clears the stack, removing all items from it.
              Inputs: None.
              Outputs: None."""
        self.items = []


class Queue:
    """ A variable-length FIFO data structure where each item is added to the
        back of the queue."""
    
    def __init__(self, *args):
        """ The constructor for the Queue class.
              Inputs: Takes any number of any objects to put in the queue.
              Outputs: None."""
        self.items = [*args]
        
    def __len__(self):
        """ A method that returns the length of the queue (an integer)."""
        return self.items.__len__()

    def enqueue(self, item):
        """ This method is used to add an item to the end / back of a queue.
              Inputs: Any item / object to be added to the end of the queue.
              Outputs: None."""
        self.items.append(item)

    def dequeue(self):
        """ This method is used to remove and return an item from the front of
            the queue.
              Inputs: None.
              Outputs: The item that was occupying the front place in the queue.
        """
        if len(self.items) == 0:
            return None
        else:
            return self.items.pop(0)

    @property
    def is_empty(self):
        """ A property that returns a Boolean value detailing whether the queue
            is empty (it has no items)."""
        return len(self.items) == 0

    def clear(self):
        """ This method completely clears the queue, removing all items from it.
              Inputs: None.
              Outputs: None."""
        self.items = []

    def remove(self):
        """ This method removes the first item in the queue and does not return
            it to the user.
              Inputs: None.
              Outputs: None."""
        self.items = self.items[1:]

    def peek(self):
        """ This method peeks at the first item in the queue without actually
            removing it from the queue.
              Inputs: None.
              Outputs: The item that was occupying the front place in the queue.
        """
        if len(self.items) == 0:
            return None
        return self.items[-1]

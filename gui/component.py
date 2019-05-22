from tkinter import *
from tkinter import ttk

class Component:
    """
    Super class for all Tk components except the root widget.
    """
    def __init__(self, parent, className, withLabel=False):
        """
        args:
            parent - Parent component
            className - Name of the component
        """
        self.parent = parent
        self.parent.children.append(self)
        self.children = []
        if withLabel:
            self.frame = ttk.LabelFrame(parent.frame)
        else:
            self.frame = ttk.Frame(parent.frame)
        self.listeners = {}
        self.className = className
        self.state = {}
        self.disabled = False
    
    def disable(self):
        self.disabled = True
    
    def enable(self):
        self.disabled = False

    def configure(self, **config):
        self.frame.configure(**config)
    
    def grid(self, **config):
        self.frame.grid(**config)
    
    def forget(self):
        self.frame.grid_forget()
    
    def addListener(self, eventName, callback):
        """Add an event listener to this component. A listener
        is a callback function which will be called when a certain
        event happens."""
        if eventName in self.listeners:
            self.listeners[eventName].append(callback)
        else:
            self.listeners[eventName] = [callback]
    
    def removeListener(self, eventName, callback):
        if eventName in self.listeners:
            self.listeners[eventName].remove(callback)
    
    def emitEvent(self, target, event):
        """Emit an event from this component. The mechanism keeps
        passing the event to parent components until it reaches
        the component with className equals to 'target'."""
        if self.disabled:
            return None
        print('Event {event} emitted by {component}'.format(event=event['name'], component=self.className))
        if target == self.className:
            self.handleEvent(event)
        else:
            self.parent.emitEvent(target, event)

    def handleEvent(self, event):
        """The event handling mechanism keeps passing event to
        all child components recursively. In this process, the
        event will be handled in every component which contains
        a matching event listener."""
        if self.disabled:
            return None
        eventName = event['name']
        if eventName in self.listeners:
            print('Event {event} handled by {component}'.format(event=event['name'], component=self.className))
            for callback in self.listeners[eventName]:
                callback(event)
        for child in self.children: # passdown
            child.handleEvent(event)
    
    def setState(self, newState=None, **kwargs):
        """Update self.state with new key-value pairs.
        'self.state' contains necessary information for
        rendering a component. self.beforeSetState is called 
        before updating the relevant states. User should implement 
        the 'self.afterSetState' method in order to re-render
        the component."""
        if self.disabled:
            return None
        self.beforeSetState()
        if isinstance(newState, dict):
            self.state.update(newState)
        self.state.update(**kwargs)
        self.afterSetState()
    
    def beforeSetState(self):
        """To be implemented by user."""
        pass
    
    def afterSetState(self):
        """To be implemented by user."""
        pass
    
    def updateStatusBar(self, message):
        """Sugar for emitting <StatusUpdate> event."""
        if self.disabled:
            return None
        event = dict(name='<StatusUpdate>', message=message)
        self.emitEvent('MainFrame', event)


from collections import defaultdict
from tokenize import Name
from re import match
from keyword import iskeyword
from inspect import getargspec

import irc.client

from nirc.errors import EventUndefinedError


class Dispatch(object):
    event_specs = dict()
    events = defaultdict(list)

    def clear(self):
        self.event_specs.clear()
        self.events.clear()

    def add_event(self, event, arguments=None):
        """
        Adds an event dispatcher.

        :param event: The event type to add
        :type event: str
        :param arguments: The arguments that this event requires all
        subscribers to accept
        :type arguments: iterable
        :returns: None
        """
        if event in self.event_specs:
            raise ValueError("'{0}' event is already defined".format(event))
        arguments = arguments or []
        for arg in arguments:
            if not match('^' + Name + '$', arg):
                raise ValueError("'{0}' is not a valid identifier".format(arg))
            elif iskeyword(arg):
                raise ValueError("'{0}' is a python keyword!".format(arg))
        self.event_specs[event] = arguments

    def subscribe(self, event):
        """
        Adds a callable to an event.  Use me as a decorator.  Return values
        from a subscriber are an error.

        :param event: The event to subscribe to
        :type event: str
        :param arguments: Defaults to call this callable with if not supplied
        :returns: A closure, ultimately None
        :rtype: callable
        """
        if event not in self.event_specs:
            raise ValueError("'{0}' event not defined".format(event))

        def decorator(f):
            if self.event_specs[event] != getargspec(f).args:
                err = "'{0}' does not define the correct arguments; {1} != {2}"
                raise ValueError(err.format(
                    f.__name__, self.event_specs[event], getargspec(f).args))
            self.events[event].append(f)
            return f
        return decorator

    def fire(self, event, **arguments):
        """
        Fires an event dispatcher.

        :param event: The event type to fire
        :type event: str
        :param arguments: arguments to call all subscribers with
        :returns: True if a function was called, False otherwise
        """
        arguments = arguments or {}
        if event not in self.event_specs:
            raise EventUndefinedError("'{0}' event not defined".format(event))
        if not set(arguments.keys()) == set(self.event_specs[event]):
            raise ValueError("unexpected arguments")
        if event in self.events:
            for ev in self.events[event]:
                ev(**arguments)
            return True
        return False


class Connection(object):
    pass


class Manager(object):
    """
    I really dont like the dispatch methods in the core IRC library, so this
    entire framework exists to build a new dispatcher.
    """
    def __init__(self):
        self.connections = {}
        self.client = irc.client.IRC()
        self.dispatch = Dispatch()
        self.client.add_global_handler(
            'all_events', self._default_handler, -100
        )

    def connection(self):
        s = self.client.server()
        con = Connection(s)
        self.connections[s] = con
        return con

    def run(self):
        self.client.process_forever()

    def _default_handler(self, s_connection, event):
        con = self.connections[s_connection]
        try:
            self.dispatch.fire(event.type, connection=con, event=event)
        except EventUndefinedError:  # pragma: no cover
            pass

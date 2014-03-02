import collections

try:  # pragma: no cover
    import unittest2 as unittest
except ImportError:  # pragma: no cover
    import unittest

try:  # pragma: no cover
    from unittest import mock
except ImportError:  # pragma: no cover
    import mock

import irc.client

import nirc.core
import nirc.errors


def _privmsg_dispatch(m):
    def f(connection, user, target, message):
        m(connection=connection, user=user, target=target, message=message)
    return f


class DispatchTestCase(unittest.TestCase):
    def setUp(self):
        self.dispatch = nirc.core.Dispatch()
        self.dispatch.clear()

    def test_init(self):
        # Did I screw up __init__?
        self.assertIsInstance(self.dispatch.event_specs, dict)
        self.assertIsInstance(self.dispatch.events, collections.defaultdict)
        self.assertIs(self.dispatch.events.default_factory, list)

    def test_clear_events(self):
        m = mock.MagicMock()
        event = 'privmsg'
        args = ['connection', 'user', 'target', 'message']
        self.dispatch.add_event(event, args)
        f = _privmsg_dispatch(m)
        closure = self.dispatch.subscribe(event)
        closure(f)
        self.dispatch.clear()
        self.assertEqual({}, self.dispatch.event_specs)
        self.assertEqual({}, self.dispatch.events)

    def test_add_event(self):
        event = 'privmsg'
        args = ['connection', 'user', 'target', 'message']
        expected = {event: args}
        self.dispatch.add_event(event, args)
        assert expected.items() <= self.dispatch.event_specs.items()

    def test_add_event_dup(self):
        event = 'privmsg'
        self.dispatch.add_event(event)
        with self.assertRaisesRegexp(ValueError, 'already defined'):
            self.dispatch.add_event(event)

    def test_add_event_keyword(self):
        with self.assertRaisesRegexp(ValueError, 'keyword'):
            self.dispatch.add_event('privmsg', ['if'])

    def test_add_event_invalid(self):
        with self.assertRaisesRegexp(ValueError, 'identifier'):
            self.dispatch.add_event('privmsg', ['not valid'])

    def test_subscribe_returns_callable(self):
        event = 'privmsg'
        args = ['connection', 'user', 'target', 'message']
        self.dispatch.add_event(event, args)
        closure = self.dispatch.subscribe('privmsg')
        assert callable(closure)

    def test_subscribe_rejects_bad_event(self):
        with self.assertRaisesRegexp(ValueError, 'not defined'):
            self.dispatch.subscribe('privmsg')

    def test_subscribe_rejects_bad_args(self):
        event = 'privmsg'
        args = ['connection', 'user', 'target', 'message']
        self.dispatch.add_event(event, args)
        closure = self.dispatch.subscribe(event)
        with self.assertRaisesRegexp(ValueError, 'correct arguments'):
            closure(mock.MagicMock().__call__)

    def test_subscribe_adds_good_args(self):
        m = mock.MagicMock()
        event = 'privmsg'
        args = ['connection', 'user', 'target', 'message']
        self.dispatch.add_event(event, args)
        f = _privmsg_dispatch(m)
        expected = {event: [f]}
        closure = self.dispatch.subscribe(event)
        closure(f)
        assert expected.items() <= self.dispatch.events.items()

    def test_fire(self):
        m = mock.MagicMock()
        event = 'privmsg'
        args = ['connection', 'user', 'target', 'message']
        passargs = {
            'connection': None,
            'user': '|Nyx|',
            'target': 'Tritium',
            'message': 'Hello There'
        }
        self.dispatch.add_event(event, args)
        f = _privmsg_dispatch(m)
        closure = self.dispatch.subscribe(event)
        closure(f)
        exit = self.dispatch.fire(event, **passargs)
        m.assert_called_once_with(**passargs)
        self.assertIs(exit, True)

    def test_fire_nocallback(self):
        event = 'privmsg'
        args = ['connection', 'user', 'target', 'message']
        passargs = {
            'connection': None,
            'user': '|Nyx|',
            'target': 'Tritium',
            'message': 'Hello There'
        }
        self.dispatch.add_event(event, args)
        exit = self.dispatch.fire(event, **passargs)
        self.assertIs(exit, False)

    def test_fire_noevent(self):
        with self.assertRaisesRegexp(
                nirc.errors.EventUndefinedError, 'not defined'):
            self.dispatch.fire('privmsg')

    def test_fire_bad_args(self):
        m = mock.MagicMock()
        event = 'privmsg'
        args = ['connection', 'user', 'target', 'message']
        self.dispatch.add_event(event, args)
        f = _privmsg_dispatch(m)
        closure = self.dispatch.subscribe(event)
        closure(f)
        with self.assertRaisesRegexp(ValueError, 'unexpected argument'):
            self.dispatch.fire(event, nick='|Nyx|')


class ManagerTestCase(unittest.TestCase):
    def setUp(self):
        self.real = {
            'IRC': irc.client.IRC,
            'Dispatch': nirc.core.Dispatch,
        }
        self.IRC = irc.client.IRC = mock.MagicMock()
        self.IRC.return_value = self.IRC
        self.IRC.server = mock.MagicMock()
        self.IRC.server.return_value = self.IRC.server
        self.IRC.process_forever = mock.MagicMock()
        self.IRC.add_global_handler = mock.MagicMock()
        self.Dispatch = nirc.core.Dispatch = mock.MagicMock()
        self.Dispatch.return_value = self.Dispatch
        self.Dispatch.fire = mock.MagicMock()
        self.manager = nirc.core.Manager()

    def tearDown(self):
        irc.client.IRC = self.real['IRC']
        nirc.core.Dispatch = self.real['Dispatch']

    def test_initialized(self):
        self.IRC.assert_called_once_with()
        self.assertEqual(self.manager.connections, [])
        self.assertIs(self.manager.client, self.IRC)
        self.assertIs(self.manager.dispatch, self.Dispatch)
        self.IRC.add_global_handler.assert_called_once_with(
            'all_events',
            self.manager._default_handler,
            -100
        )

    def test_run_calls_process_forever(self):
        self.manager.run()
        self.IRC.process_forever.assert_called_once_with()

    def test_connection_calls_server(self):
        self.manager.connection()
        self.IRC.server.assert_called_once_with()

    def test_connection_adds_to_connections(self):
        self.manager.connection()
        self.assertEqual(
            self.manager.connections,
            [self.IRC.server],
        )

    def test_handle_event_fires(self):
        con = self.manager.connection()
        scon = self.IRC.server
        ev = irc.client.Event(
            'any',
            irc.client.NickMask('|Nyx|!alexis@venom.sdamon.com'),
            None,
            None
        )
        self.manager._default_handler(scon, ev)
        self.Dispatch.fire.assert_called_once_with(
            'any',
            connection=con,
            event=ev
        )

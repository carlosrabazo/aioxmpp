########################################################################
# File name: test_service.py
# This file is part of: aioxmpp
#
# LICENSE
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this program.  If not, see
# <http://www.gnu.org/licenses/>.
#
########################################################################
import abc
import asyncio
import contextlib
import itertools
import logging
import unittest

import aioxmpp.callbacks as callbacks
import aioxmpp.service as service

from aioxmpp.testutils import (
    run_coroutine,
    CoroutineMock,
)


class TestServiceMeta(unittest.TestCase):
    def setUp(self):
        self.descriptor_cm = unittest.mock.Mock()

        class FooDescriptor(service.Descriptor):
            def __init__(self, *, deps=[]):
                super().__init__()
                self._deps = list(deps)

            @property
            def required_dependencies(self):
                return list(self._deps)

            def init_cm(self, instance):
                return self.descriptor_cm(instance)

        self.FooDescriptor = FooDescriptor

    def tearDown(self):
        del self.FooDescriptor

    def test_inherits_from_ABCMeta(self):
        self.assertTrue(issubclass(service.Meta, abc.ABCMeta))

    def test_ordering_attributes(self):
        class Foo(metaclass=service.Meta):
            pass

        self.assertSetEqual(
            set(),
            Foo.ORDER_BEFORE
        )
        self.assertSetEqual(
            set(),
            Foo.ORDER_AFTER
        )

    def test_configure_ordering(self):
        class Foo(metaclass=service.Meta):
            pass

        class Bar(metaclass=service.Meta):
            ORDER_BEFORE = [Foo]

        self.assertSetEqual(
            {Foo},
            Bar.ORDER_BEFORE
        )
        self.assertSetEqual(
            set(),
            Bar.ORDER_AFTER
        )
        self.assertSetEqual(
            {Bar},
            Foo.ORDER_AFTER
        )
        self.assertSetEqual(
            set(),
            Foo.ORDER_BEFORE
        )

    def test_transitive_before_ordering(self):
        class Foo(metaclass=service.Meta):
            pass

        class Bar(metaclass=service.Meta):
            ORDER_BEFORE = [Foo]

        class Baz(metaclass=service.Meta):
            ORDER_BEFORE = [Bar]

        self.assertSetEqual(
            {Foo},
            Bar.ORDER_BEFORE
        )
        self.assertSetEqual(
            {Foo, Bar},
            Baz.ORDER_BEFORE
        )
        self.assertSetEqual(
            {Bar, Baz},
            Foo.ORDER_AFTER
        )
        self.assertSetEqual(
            {Baz},
            Bar.ORDER_AFTER
        )
        self.assertSetEqual(
            set(),
            Foo.ORDER_BEFORE
        )
        self.assertSetEqual(
            set(),
            Baz.ORDER_AFTER
        )

    def test_transitive_after_ordering(self):
        class Foo(metaclass=service.Meta):
            pass

        class Bar(metaclass=service.Meta):
            ORDER_AFTER = [Foo]

        class Baz(metaclass=service.Meta):
            ORDER_AFTER = [Bar]

        self.assertSetEqual(
            {Foo},
            Bar.ORDER_AFTER
        )
        self.assertSetEqual(
            {Foo, Bar},
            Baz.ORDER_AFTER
        )
        self.assertSetEqual(
            {Bar, Baz},
            Foo.ORDER_BEFORE
        )
        self.assertSetEqual(
            {Baz},
            Bar.ORDER_BEFORE
        )
        self.assertSetEqual(
            set(),
            Foo.ORDER_AFTER
        )
        self.assertSetEqual(
            set(),
            Baz.ORDER_BEFORE
        )

    def test_loop_detect(self):
        class Foo(metaclass=service.Meta):
            pass

        class Bar(metaclass=service.Meta):
            ORDER_AFTER = [Foo]

        with self.assertRaisesRegex(
                ValueError,
                "dependency loop: Fnord loops through .*\.(Foo|Bar)"):

            class Fnord(metaclass=service.Meta):
                ORDER_BEFORE = [Foo]
                ORDER_AFTER = [Bar]

            print(Fnord.ORDER_BEFORE)
            print(Fnord.ORDER_AFTER)

    def test_partial_dependency_ordering_puts_earliest_first(self):
        class Foo(metaclass=service.Meta):
            pass

        class Bar(metaclass=service.Meta):
            ORDER_BEFORE = [Foo]

        class Baz(metaclass=service.Meta):
            ORDER_BEFORE = [Bar]

        class Fourth(metaclass=service.Meta):
            ORDER_BEFORE = [Bar]

        self.assertLess(Baz, Bar)
        self.assertLess(Fourth, Bar)
        self.assertLess(Bar, Foo)
        self.assertLess(Baz, Foo)
        self.assertLess(Fourth, Foo)

        self.assertLessEqual(Baz, Bar)
        self.assertLessEqual(Fourth, Bar)
        self.assertLessEqual(Bar, Foo)
        self.assertLessEqual(Baz, Foo)
        self.assertLessEqual(Fourth, Foo)

        self.assertGreater(Foo, Bar)
        self.assertGreater(Foo, Baz)
        self.assertGreater(Foo, Fourth)
        self.assertGreater(Bar, Baz)
        self.assertGreater(Bar, Fourth)

        self.assertGreaterEqual(Foo, Bar)
        self.assertGreaterEqual(Foo, Baz)
        self.assertGreaterEqual(Foo, Fourth)
        self.assertGreaterEqual(Bar, Baz)
        self.assertGreaterEqual(Bar, Fourth)

        services = [Foo, Bar, Baz, Fourth]

        for a, b in itertools.product(services, services):
            if a is b:
                self.assertEqual(a, b)
                self.assertFalse(a != b)
            else:
                self.assertNotEqual(a, b)
                self.assertFalse(a == b)

        services.sort()

        self.assertSequenceEqual(
            [Baz, Fourth, Bar, Foo],
            services
        )

        services = [Foo, Bar, Fourth, Baz]
        services.sort()

        self.assertSequenceEqual(
            [Fourth, Baz, Bar, Foo],
            services
        )

    def test_simple_inheritance_inherit_ordering(self):
        class Foo(metaclass=service.Meta):
            pass

        class Bar(metaclass=service.Meta):
            pass

        class A(metaclass=service.Meta):
            ORDER_BEFORE = [Foo]
            ORDER_AFTER = [Bar]

        class B(A):
            pass

        self.assertSetEqual(A.ORDER_BEFORE, B.ORDER_BEFORE)
        self.assertSetEqual(A.ORDER_AFTER, B.ORDER_AFTER)

        self.assertIsNot(A.ORDER_BEFORE, B.ORDER_BEFORE)
        self.assertIsNot(A.ORDER_AFTER, B.ORDER_AFTER)

    def test_inheritance_ignores_non_service_classes(self):
        class Foo(metaclass=service.Meta):
            pass

        class Bar:
            ORDER_BEFORE = [Foo]

        class Baz(Bar, metaclass=service.Meta):
            pass

        self.assertSetEqual(set(), Baz.ORDER_BEFORE)

    def test_diamond_inheritance(self):
        class Foo(metaclass=service.Meta):
            pass

        class Bar(metaclass=service.Meta):
            pass

        class Baz(metaclass=service.Meta):
            pass

        class A(metaclass=service.Meta):
            ORDER_BEFORE = [Foo]

        class B1(A):
            ORDER_AFTER = [Bar]

        class B2(A):
            ORDER_BEFORE = [Baz]

        class D(B1, B2):
            pass

        self.assertSetEqual(
            {A, B1, B2, D},
            Foo.ORDER_AFTER
        )
        self.assertSetEqual(
            {B1, D},
            Bar.ORDER_BEFORE
        )
        self.assertSetEqual(
            {B2, D},
            Baz.ORDER_AFTER
        )
        self.assertSetEqual(
            {Foo, Baz},
            D.ORDER_BEFORE
        )
        self.assertSetEqual(
            {Foo, Baz},
            B2.ORDER_BEFORE
        )
        self.assertSetEqual(
            {Bar},
            D.ORDER_AFTER
        )
        self.assertSetEqual(
            {Bar},
            B1.ORDER_AFTER
        )

    def test_inherit_dependencies_False(self):
        class Foo(metaclass=service.Meta):
            pass

        class Bar(metaclass=service.Meta):
            pass

        class A(metaclass=service.Meta):
            ORDER_BEFORE = [Foo]
            ORDER_AFTER = [Bar]

        class B(A, inherit_dependencies=False):
            ORDER_AFTER = [Foo]

        self.assertSetEqual(
            {A},
            Foo.ORDER_AFTER
        )
        self.assertSetEqual(
            {B},
            Foo.ORDER_BEFORE
        )
        self.assertSetEqual(
            {Foo, A, Bar},
            B.ORDER_AFTER
        )
        self.assertSetEqual(
            set(),
            B.ORDER_BEFORE
        )

    def test_support_pre_0_3_attributes_on_class(self):
        class Foo(metaclass=service.Meta):
            pass

        class Bar(metaclass=service.Meta):
            pass

        class A(metaclass=service.Meta):
            SERVICE_BEFORE = [Foo]
            SERVICE_AFTER = [Bar]

        class B(A, inherit_dependencies=False):
            SERVICE_AFTER = [Foo]

        self.assertSetEqual(
            {A},
            Foo.ORDER_AFTER
        )
        self.assertSetEqual(
            {B},
            Foo.ORDER_BEFORE
        )
        self.assertSetEqual(
            {Foo, A, Bar},
            B.ORDER_AFTER
        )
        self.assertSetEqual(
            set(),
            B.ORDER_BEFORE
        )

    def test_support_pre_0_3_attributes_on_read(self):
        class Foo(metaclass=service.Meta):
            pass

        self.assertIs(Foo.ORDER_BEFORE, Foo.SERVICE_BEFORE)
        self.assertIs(Foo.ORDER_AFTER, Foo.SERVICE_AFTER)

    def test_support_pre_0_3_attributes_raise_if_both_are_given(self):
        class Foo(metaclass=service.Meta):
            pass

        with self.assertRaisesRegex(ValueError, "mixes old and new"):
            class Bar1(metaclass=service.Meta):
                ORDER_BEFORE = [Foo]
                SERVICE_BEFORE = [Foo]

        with self.assertRaisesRegex(ValueError, "mixes old and new"):
            class Bar2(metaclass=service.Meta):
                ORDER_AFTER = [Foo]
                SERVICE_AFTER = [Foo]

        with self.assertRaisesRegex(ValueError, "mixes old and new"):
            class Bar3(metaclass=service.Meta):
                ORDER_BEFORE = [Foo]
                SERVICE_AFTER = [Foo]

    def test_support_pre_0_3_attributes_with_deprecation_warning(self):
        class Foo(metaclass=service.Meta):
            pass

        with unittest.mock.patch("warnings.warn") as warn:
            class Bar1(metaclass=service.Meta):
                SERVICE_BEFORE = [Foo]

            class Bar2(metaclass=service.Meta):
                SERVICE_AFTER = [Foo]

        s = "SERVICE_BEFORE/AFTER used on class; use ORDER_BEFORE/AFTER"
        self.assertSequenceEqual(
            warn.mock_calls,
            [
                unittest.mock.call(s, DeprecationWarning),
                unittest.mock.call(s, DeprecationWarning),
            ]
        )

    def test_collect_handlers(self):
        class ObjectWithHandlers:
            def __init__(self, handlers=[]):
                self._aioxmpp_service_handlers = set(handlers)

        class Foo(metaclass=service.Meta):
            x = ObjectWithHandlers(
                [
                    service.HandlerSpec(
                        unittest.mock.sentinel.k1,
                        is_unique=True,
                    ),
                    service.HandlerSpec(
                        unittest.mock.sentinel.k2,
                        is_unique=False,
                    ),
                ]
            )

        self.assertCountEqual(
            Foo.SERVICE_HANDLERS,
            (
                (unittest.mock.sentinel.k1, Foo.x),
                (unittest.mock.sentinel.k2, Foo.x),
            ),
        )

        self.assertIsInstance(Foo.SERVICE_HANDLERS, tuple)

    def test_reject_missing_dependencies(self):
        class ObjectWithHandlers:
            def __init__(self, handlers=[]):
                self._aioxmpp_service_handlers = set(handlers)

        with self.assertRaisesRegex(
                TypeError,
                r"decorator requires dependency .* but it is not declared"):
            class Foo(metaclass=service.Meta):
                x = ObjectWithHandlers(
                    [
                        service.HandlerSpec(
                            unittest.mock.sentinel.k1,
                            is_unique=True,
                            require_deps=(unittest.mock.sentinel.nonexistent,)
                        ),
                    ]
                )

    def test_allow_properly_declared_dependencies(self):
        class ObjectWithHandlers:
            def __init__(self, handlers=[]):
                self._aioxmpp_service_handlers = set(handlers)

        class Other(metaclass=service.Meta):
            pass

        class Foo(metaclass=service.Meta):
            ORDER_AFTER = [Other]

            x = ObjectWithHandlers(
                [
                    service.HandlerSpec(
                        unittest.mock.sentinel.k1,
                        is_unique=True,
                        require_deps=(Other,)
                    ),
                ]
            )

    def test_reject_duplicate_handlers_on_different_objects(self):
        class ObjectWithHandlers:
            def __init__(self, handlers=[]):
                self._aioxmpp_service_handlers = set(handlers)

        with self.assertRaisesRegex(
                TypeError,
                "handler conflict between .* and .*: both want to use .*"):

            class Foo(metaclass=service.Meta):
                x = ObjectWithHandlers(
                    [
                        service.HandlerSpec(
                            unittest.mock.sentinel.k1
                        ),
                        service.HandlerSpec(
                            unittest.mock.sentinel.k2
                        ),
                    ]
                )

                y = ObjectWithHandlers(
                    [
                        service.HandlerSpec(
                            unittest.mock.sentinel.k2
                        ),
                        service.HandlerSpec(
                            unittest.mock.sentinel.k3
                        )
                    ]
                )

    def test_allow_duplicate_handlers_on_different_objects_for_non_unique(self):
        class ObjectWithHandlers:
            def __init__(self, handlers=[]):
                self._aioxmpp_service_handlers = set(handlers)

        class Foo(metaclass=service.Meta):
            x = ObjectWithHandlers(
                [
                    service.HandlerSpec(
                        unittest.mock.sentinel.k1
                    ),
                    service.HandlerSpec(
                        unittest.mock.sentinel.k2,
                        is_unique=False,
                    ),
                ]
            )

            y = ObjectWithHandlers(
                [
                    service.HandlerSpec(
                        unittest.mock.sentinel.k2,
                        is_unique=False,
                    ),
                    service.HandlerSpec(
                        unittest.mock.sentinel.k3
                    )
                ]
            )

    def test_reject_inheritance_from_class_with_handlers(self):
        class ObjectWithHandlers:
            def __init__(self, handlers=[]):
                self._aioxmpp_service_handlers = set(handlers)

        class Foo(metaclass=service.Meta):
            x = ObjectWithHandlers(
                [
                    service.HandlerSpec(
                        unittest.mock.sentinel.k1
                    ),
                ]
            )

        with self.assertRaisesRegex(
                TypeError,
                r"inheritance from service class with handlers is forbidden"):
            class Bar(Foo):
                pass

    def test_collect_descriptors(self):
        descriptor = self.FooDescriptor()

        class Foo(metaclass=service.Meta):
            x = descriptor

        self.assertCountEqual(
            Foo.SERVICE_DESCRIPTORS,
            (
                descriptor,
            ),
        )

    def test_reject_inheritance_from_class_with_descriptors(self):
        class Foo(metaclass=service.Meta):
            x = self.FooDescriptor()

        with self.assertRaisesRegex(
                TypeError,
                r"inheritance from service class with descriptors is "
                "forbidden"):
            class Bar(Foo):
                pass

    def test_reject_missing_descriptor_dependencies(self):
        with self.assertRaisesRegex(
                TypeError,
                r"descriptor requires dependency .* but it is not declared"):
            class Foo(metaclass=service.Meta):
                x = self.FooDescriptor(deps=[unittest.mock.sentinel.foo])

    def test_allow_properly_declared_descriptor_dependencies(self):
        class Other(metaclass=service.Meta):
            pass

        class Foo(metaclass=service.Meta):
            ORDER_AFTER = [Other]

            x = self.FooDescriptor(deps=[Other])


class TestService(unittest.TestCase):
    def test_is_Meta(self):
        self.assertIsInstance(
            service.Service,
            service.Meta
        )

    def test_automatic_logger(self):
        class Service(service.Service):
            pass

        s = Service(None)
        self.assertIsInstance(s.logger, logging.Logger)
        self.assertEqual(
            "tests.test_service.TestService"
            ".test_automatic_logger.<locals>.Service",
            s.logger.name
        )

    def test_custom_logger(self):
        l = logging.getLogger("foo")
        s = service.Service(None, logger_base=l)

        self.assertEqual(s.logger, l.getChild("service.Service"))

    def test_client(self):
        o = object()
        s = service.Service(o)
        self.assertIs(s.client, o)

        with self.assertRaises(AttributeError):
            s.client = o

    def test_shutdown(self):
        o = object()
        s = service.Service(o)

        def coro():
            return
            yield

        with unittest.mock.patch.object(s, "_shutdown") as _shutdown:
            _shutdown.return_value = coro()
            run_coroutine(s.shutdown())

        self.assertSequenceEqual(
            [
                unittest.mock.call(),
            ],
            _shutdown.mock_calls
        )

    def test_setup_handler_context(self):
        res1 = unittest.mock.Mock()
        res2 = unittest.mock.Mock()

        base = unittest.mock.Mock()

        self.maxDiff = None

        class ObjectWithHandlers:
            def __init__(self, handlers=[]):
                self._aioxmpp_service_handlers = set(handlers)

            def __get__(self, instance, owner):
                if instance is None:
                    return self
                return (unittest.mock.sentinel.got, self)

        class ServiceWithHandlers(service.Service):
            x = ObjectWithHandlers(
                [
                    service.HandlerSpec((res1, ()), is_unique=False),
                    service.HandlerSpec((res2, ("foo",))),
                ]
            )

            y = ObjectWithHandlers(
                [
                    service.HandlerSpec((res2, ("bar",))),
                ]
            )

        client = unittest.mock.Mock()

        with unittest.mock.patch("contextlib.ExitStack",
                                 new=base.ExitStack) as ExitStack:
            s = ServiceWithHandlers(client)

        print(ServiceWithHandlers.SERVICE_HANDLERS)

        self.assertCountEqual(
            res1.mock_calls,
            [
                unittest.mock.call(
                    s,
                    client.stream,
                    (unittest.mock.sentinel.got, ServiceWithHandlers.x)
                )
            ]
        )

        self.assertCountEqual(
            res2.mock_calls,
            [
                unittest.mock.call(
                    s,
                    client.stream,
                    (unittest.mock.sentinel.got, ServiceWithHandlers.x),
                    "foo",
                ),
                unittest.mock.call(
                    s,
                    client.stream,
                    (unittest.mock.sentinel.got, ServiceWithHandlers.y),
                    "bar",
                )
            ]
        )

        self.assertSequenceEqual(
            ExitStack.mock_calls,
            [
                unittest.mock.call(),
            ] + [
                unittest.mock.call().enter_context(
                    handler_cm()
                )
                for (handler_cm, args), obj
                in ServiceWithHandlers.SERVICE_HANDLERS
            ]
        )

        base.mock_calls.clear()

        base._shutdown = CoroutineMock()

        with unittest.mock.patch.object(s, "_shutdown", new=base._shutdown):
            run_coroutine(s.shutdown())

        self.assertSequenceEqual(
            base.mock_calls,
            [
                unittest.mock.call._shutdown(),
                unittest.mock.call.ExitStack().close(),
            ]
        )

    def test_dependencies(self):
        s = service.Service(
            unittest.mock.sentinel.client,
            dependencies=unittest.mock.sentinel.deps
        )
        self.assertEqual(
            s.dependencies,
            unittest.mock.sentinel.deps,
        )

    def test_dependencies_is_not_writable(self):
        s = service.Service(
            unittest.mock.sentinel.client,
            dependencies=unittest.mock.sentinel.deps
        )
        with self.assertRaises(AttributeError):
            s.dependencies = unittest.mock.sentinel.deps


class Test_apply_iq_handler(unittest.TestCase):
    def test_uses_stream_iq_handler(self):
        with unittest.mock.patch("aioxmpp.stream.iq_handler") as iq_handler:
            service._apply_iq_handler(
                unittest.mock.sentinel.instance,
                unittest.mock.sentinel.stream,
                unittest.mock.sentinel.func,
                unittest.mock.sentinel.type_,
                unittest.mock.sentinel.payload_cls,
            )

        iq_handler.assert_called_with(
            unittest.mock.sentinel.stream,
            unittest.mock.sentinel.type_,
            unittest.mock.sentinel.payload_cls,
            unittest.mock.sentinel.func,
        )


class Test_apply_message_handler(unittest.TestCase):
    def test_uses_stream_message_handler(self):
        with unittest.mock.patch(
                "aioxmpp.stream.message_handler") as message_handler:
            service._apply_message_handler(
                unittest.mock.sentinel.instance,
                unittest.mock.sentinel.stream,
                unittest.mock.sentinel.func,
                unittest.mock.sentinel.type_,
                unittest.mock.sentinel.from_,
            )

        message_handler.assert_called_with(
            unittest.mock.sentinel.stream,
            unittest.mock.sentinel.type_,
            unittest.mock.sentinel.from_,
            unittest.mock.sentinel.func,
        )


class Test_apply_presence_handler(unittest.TestCase):
    def test_uses_stream_presence_handler(self):
        with unittest.mock.patch(
                "aioxmpp.stream.presence_handler") as presence_handler:
            service._apply_presence_handler(
                unittest.mock.sentinel.instance,
                unittest.mock.sentinel.stream,
                unittest.mock.sentinel.func,
                unittest.mock.sentinel.type_,
                unittest.mock.sentinel.from_,
            )

        presence_handler.assert_called_with(
            unittest.mock.sentinel.stream,
            unittest.mock.sentinel.type_,
            unittest.mock.sentinel.from_,
            unittest.mock.sentinel.func,
        )


class Test_apply_inbound_message_filter(unittest.TestCase):
    def test_uses_stream_stanza_filter(self):
        stream = unittest.mock.Mock()

        with unittest.mock.patch(
                "aioxmpp.stream.stanza_filter") as stanza_filter:
            service._apply_inbound_message_filter(
                unittest.mock.sentinel.instance,
                stream,
                unittest.mock.sentinel.func,
            )

        stanza_filter.assert_called_with(
            stream.service_inbound_message_filter,
            unittest.mock.sentinel.func,
            type(unittest.mock.sentinel.instance),
        )


class Test_apply_inbound_presence_filter(unittest.TestCase):
    def test_uses_stream_stanza_filter(self):
        stream = unittest.mock.Mock()

        with unittest.mock.patch(
                "aioxmpp.stream.stanza_filter") as stanza_filter:
            service._apply_inbound_presence_filter(
                unittest.mock.sentinel.instance,
                stream,
                unittest.mock.sentinel.func,
            )

        stanza_filter.assert_called_with(
            stream.service_inbound_presence_filter,
            unittest.mock.sentinel.func,
            type(unittest.mock.sentinel.instance),
        )


class Test_apply_outbound_message_filter(unittest.TestCase):
    def test_uses_stream_stanza_filter(self):
        stream = unittest.mock.Mock()

        with unittest.mock.patch(
                "aioxmpp.stream.stanza_filter") as stanza_filter:
            service._apply_outbound_message_filter(
                unittest.mock.sentinel.instance,
                stream,
                unittest.mock.sentinel.func,
            )

        stanza_filter.assert_called_with(
            stream.service_outbound_message_filter,
            unittest.mock.sentinel.func,
            type(unittest.mock.sentinel.instance),
        )


class Test_apply_outbound_presence_filter(unittest.TestCase):
    def test_uses_stream_stanza_filter(self):
        stream = unittest.mock.Mock()

        with unittest.mock.patch(
                "aioxmpp.stream.stanza_filter") as stanza_filter:
            service._apply_outbound_presence_filter(
                unittest.mock.sentinel.instance,
                stream,
                unittest.mock.sentinel.func,
            )

        stanza_filter.assert_called_with(
            stream.service_outbound_presence_filter,
            unittest.mock.sentinel.func,
            type(unittest.mock.sentinel.instance),
        )


class Test_apply_connect_depsignal(unittest.TestCase):
    def test_uses_dependencies(self):
        instance = unittest.mock.MagicMock()
        dependency = unittest.mock.Mock()
        instance.dependencies.__getitem__.return_value = dependency

        result = service._apply_connect_depsignal(
            instance,
            unittest.mock.sentinel.stream,
            unittest.mock.sentinel.func,
            unittest.mock.sentinel.dependency,
            "signal_name",
            unittest.mock.sentinel.mode,
        )

        instance.dependencies.__getitem__.assert_called_with(
            unittest.mock.sentinel.dependency,
        )

        self.assertSequenceEqual(
            dependency.mock_calls,
            [
                unittest.mock.call.signal_name.context_connect(
                    unittest.mock.sentinel.func,
                    unittest.mock.sentinel.mode,
                )
            ]
        )

        self.assertEqual(
            result,
            dependency.signal_name.context_connect(),
        )

    def test_does_not_pass_mode_if_it_is_None(self):
        instance = unittest.mock.MagicMock()
        dependency = unittest.mock.Mock()
        instance.dependencies.__getitem__.return_value = dependency

        result = service._apply_connect_depsignal(
            instance,
            unittest.mock.sentinel.stream,
            unittest.mock.sentinel.func,
            unittest.mock.sentinel.dependency,
            "signal_name",
            None,
        )

        instance.dependencies.__getitem__.assert_called_with(
            unittest.mock.sentinel.dependency,
        )

        self.assertSequenceEqual(
            dependency.mock_calls,
            [
                unittest.mock.call.signal_name.context_connect(
                    unittest.mock.sentinel.func,
                )
            ]
        )

        self.assertEqual(
            result,
            dependency.signal_name.context_connect(),
        )


class Testadd_handler_spec(unittest.TestCase):
    def test_adds_magic_attribute(self):
        target = unittest.mock.Mock(spec=[])

        self.assertFalse(
            service.has_magic_attr(target),
        )

        service.add_handler_spec(
            target,
            unittest.mock.sentinel.foo,
        )

        self.assertTrue(
            service.has_magic_attr(target),
        )

        self.assertIn(
            unittest.mock.sentinel.foo,
            service.get_magic_attr(target),
        )

    def test_preserves_existing_magic_attr(self):
        target = unittest.mock.Mock(spec=[])
        service.automake_magic_attr(target)
        service.get_magic_attr(target).add(
            unittest.mock.sentinel.bar
        )

        self.assertTrue(
            service.has_magic_attr(target),
        )

        service.add_handler_spec(
            target,
            unittest.mock.sentinel.foo,
        )

        self.assertTrue(
            service.has_magic_attr(target),
        )

        self.assertCountEqual(
            service.get_magic_attr(target),
            [
                unittest.mock.sentinel.foo,
                unittest.mock.sentinel.bar,
            ]
        )


class Testiq_handler(unittest.TestCase):
    def setUp(self):
        self.decorator = service.iq_handler(
            unittest.mock.sentinel.type_,
            unittest.mock.sentinel.payload_cls
        )

    def tearDown(self):
        del self.decorator

    def test_works_as_decorator(self):
        @asyncio.coroutine
        def coro():
            pass

        self.assertIs(
            coro,
            self.decorator(coro),
        )

    def test_adds_magic_attribute(self):
        @asyncio.coroutine
        def coro():
            pass

        self.decorator(coro)

        self.assertTrue(hasattr(coro, "_aioxmpp_service_handlers"))

    def test_adds__apply_iq_handler_entry(self):
        @asyncio.coroutine
        def coro():
            pass

        self.decorator(coro)

        self.assertIn(
            service.HandlerSpec(
                (service._apply_iq_handler,
                 (unittest.mock.sentinel.type_,
                  unittest.mock.sentinel.payload_cls)),
                is_unique=True,
                require_deps=(),
            ),
            coro._aioxmpp_service_handlers
        )

    def test_stacks_with_other_effects(self):
        @asyncio.coroutine
        def coro():
            pass

        coro._aioxmpp_service_handlers = {"foo"}

        self.decorator(coro)

        self.assertIn(
            service.HandlerSpec(
                (service._apply_iq_handler,
                 (unittest.mock.sentinel.type_,
                  unittest.mock.sentinel.payload_cls)),
                is_unique=True,
                require_deps=(),
            ),
            coro._aioxmpp_service_handlers
        )

        self.assertIn(
            "foo",
            coro._aioxmpp_service_handlers,
        )

    def test_requires_coroutine(self):
        with unittest.mock.patch(
                "asyncio.iscoroutinefunction") as iscoroutinefunction:
            iscoroutinefunction.return_value = False

            with self.assertRaisesRegex(
                    TypeError,
                    "a coroutine function is required"):
                self.decorator(unittest.mock.sentinel.coro)

        iscoroutinefunction.assert_called_with(
            unittest.mock.sentinel.coro,
        )

    def test_works_with_is_iq_handler(self):
        @asyncio.coroutine
        def coro():
            pass

        self.assertFalse(
            service.is_iq_handler(
                unittest.mock.sentinel.type_,
                unittest.mock.sentinel.payload_cls,
                coro,
            )
        )

        self.decorator(coro)

        self.assertTrue(
            service.is_iq_handler(
                unittest.mock.sentinel.type_,
                unittest.mock.sentinel.payload_cls,
                coro,
            )
        )


class Testmessage_handler(unittest.TestCase):
    def setUp(self):
        self.decorator = service.message_handler(
            unittest.mock.sentinel.type_,
            unittest.mock.sentinel.from_
        )

    def tearDown(self):
        del self.decorator

    def test_works_as_decorator(self):
        def cb():
            pass

        self.assertIs(
            cb,
            self.decorator(cb),
        )

    def test_adds_magic_attribute(self):
        def cb():
            pass

        self.decorator(cb)

        self.assertTrue(hasattr(cb, "_aioxmpp_service_handlers"))

    def test_adds__apply_message_handler_entry(self):
        def cb():
            pass

        self.decorator(cb)

        self.assertIn(
            service.HandlerSpec(
                (service._apply_message_handler,
                 (unittest.mock.sentinel.type_,
                  unittest.mock.sentinel.from_)),
                is_unique=True,
                require_deps=(),
            ),
            cb._aioxmpp_service_handlers
        )

    def test_stacks_with_other_effects(self):
        def cb():
            pass

        cb._aioxmpp_service_handlers = {"foo"}

        self.decorator(cb)

        self.assertIn(
            service.HandlerSpec(
                (service._apply_message_handler,
                 (unittest.mock.sentinel.type_,
                  unittest.mock.sentinel.from_)),
                is_unique=True,
                require_deps=(),
            ),
            cb._aioxmpp_service_handlers
        )

        self.assertIn(
            "foo",
            cb._aioxmpp_service_handlers,
        )

    def test_requires_non_coroutine(self):
        with unittest.mock.patch(
                "asyncio.iscoroutinefunction") as iscoroutinefunction:
            iscoroutinefunction.return_value = True

            with self.assertRaisesRegex(
                    TypeError,
                    "must not be a coroutine function"):
                self.decorator(unittest.mock.sentinel.cb)

        iscoroutinefunction.assert_called_with(
            unittest.mock.sentinel.cb,
        )

    def test_works_with_is_message_handler(self):
        def cb():
            pass

        self.assertFalse(
            service.is_message_handler(
                unittest.mock.sentinel.type_,
                unittest.mock.sentinel.from_,
                cb,
            )
        )

        self.decorator(cb)

        self.assertTrue(
            service.is_message_handler(
                unittest.mock.sentinel.type_,
                unittest.mock.sentinel.from_,
                cb,
            )
        )


class Testpresence_handler(unittest.TestCase):
    def setUp(self):
        self.decorator = service.presence_handler(
            unittest.mock.sentinel.type_,
            unittest.mock.sentinel.from_
        )

    def tearDown(self):
        del self.decorator

    def test_works_as_decorator(self):
        def cb():
            pass

        self.assertIs(
            cb,
            self.decorator(cb),
        )

    def test_adds_magic_attribute(self):
        def cb():
            pass

        self.decorator(cb)

        self.assertTrue(hasattr(cb, "_aioxmpp_service_handlers"))

    def test_adds__apply_presence_handler_entry(self):
        def cb():
            pass

        self.decorator(cb)

        self.assertIn(
            service.HandlerSpec(
                (service._apply_presence_handler,
                 (unittest.mock.sentinel.type_,
                  unittest.mock.sentinel.from_)),
                is_unique=True,
                require_deps=(),
            ),
            cb._aioxmpp_service_handlers
        )

    def test_stacks_with_other_effects(self):
        def cb():
            pass

        cb._aioxmpp_service_handlers = {"foo"}

        self.decorator(cb)

        self.assertIn(
            service.HandlerSpec(
                (service._apply_presence_handler,
                 (unittest.mock.sentinel.type_,
                  unittest.mock.sentinel.from_)),
                is_unique=True,
                require_deps=(),
            ),
            cb._aioxmpp_service_handlers
        )

        self.assertIn(
            "foo",
            cb._aioxmpp_service_handlers,
        )

    def test_requires_non_coroutine(self):
        with unittest.mock.patch(
                "asyncio.iscoroutinefunction") as iscoroutinefunction:
            iscoroutinefunction.return_value = True

            with self.assertRaisesRegex(
                    TypeError,
                    "must not be a coroutine function"):
                self.decorator(unittest.mock.sentinel.cb)

        iscoroutinefunction.assert_called_with(
            unittest.mock.sentinel.cb,
        )

    def test_works_with_is_presence_handler(self):
        def cb():
            pass

        self.assertFalse(
            service.is_presence_handler(
                unittest.mock.sentinel.type_,
                unittest.mock.sentinel.from_,
                cb,
            )
        )

        self.decorator(cb)

        self.assertTrue(
            service.is_presence_handler(
                unittest.mock.sentinel.type_,
                unittest.mock.sentinel.from_,
                cb,
            )
        )


class Testinbound_message_filter(unittest.TestCase):
    def setUp(self):
        self.decorator = service.inbound_message_filter

    def tearDown(self):
        del self.decorator

    def test_works_as_decorator(self):
        def cb():
            pass

        self.assertIs(
            cb,
            self.decorator(cb),
        )

    def test_adds_magic_attribute(self):
        def cb():
            pass

        self.decorator(cb)

        self.assertTrue(hasattr(cb, "_aioxmpp_service_handlers"))

    def test_adds__apply_inbound_message_filter_entry(self):
        def cb():
            pass

        self.decorator(cb)

        self.assertIn(
            service.HandlerSpec(
                (service._apply_inbound_message_filter, ()),
                is_unique=True,
                require_deps=(),
            ),
            cb._aioxmpp_service_handlers
        )

    def test_stacks_with_other_effects(self):
        def cb():
            pass

        cb._aioxmpp_service_handlers = {"foo"}

        self.decorator(cb)

        self.assertIn(
            service.HandlerSpec(
                (service._apply_inbound_message_filter, ()),
                is_unique=True,
                require_deps=(),
            ),
            cb._aioxmpp_service_handlers
        )

        self.assertIn(
            "foo",
            cb._aioxmpp_service_handlers,
        )

    def test_requires_non_coroutine(self):
        with unittest.mock.patch(
                "asyncio.iscoroutinefunction") as iscoroutinefunction:
            iscoroutinefunction.return_value = True

            with self.assertRaisesRegex(
                    TypeError,
                    "must not be a coroutine function"):
                self.decorator(unittest.mock.sentinel.cb)

        iscoroutinefunction.assert_called_with(
            unittest.mock.sentinel.cb,
        )


class Testinbound_presence_filter(unittest.TestCase):
    def setUp(self):
        self.decorator = service.inbound_presence_filter

    def tearDown(self):
        del self.decorator

    def test_works_as_decorator(self):
        def cb():
            pass

        self.assertIs(
            cb,
            self.decorator(cb),
        )

    def test_adds_magic_attribute(self):
        def cb():
            pass

        self.decorator(cb)

        self.assertTrue(hasattr(cb, "_aioxmpp_service_handlers"))

    def test_adds__apply_inbound_presence_filter_entry(self):
        def cb():
            pass

        self.decorator(cb)

        self.assertIn(
            service.HandlerSpec(
                (service._apply_inbound_presence_filter, ()),
                is_unique=True,
                require_deps=(),
            ),
            cb._aioxmpp_service_handlers
        )

    def test_stacks_with_other_effects(self):
        def cb():
            pass

        cb._aioxmpp_service_handlers = {"foo"}

        self.decorator(cb)

        self.assertIn(
            service.HandlerSpec(
                (service._apply_inbound_presence_filter, ()),
                is_unique=True,
                require_deps=(),
            ),
            cb._aioxmpp_service_handlers
        )

        self.assertIn(
            "foo",
            cb._aioxmpp_service_handlers,
        )

    def test_requires_non_coroutine(self):
        with unittest.mock.patch(
                "asyncio.iscoroutinefunction") as iscoroutinefunction:
            iscoroutinefunction.return_value = True

            with self.assertRaisesRegex(
                    TypeError,
                    "must not be a coroutine function"):
                self.decorator(unittest.mock.sentinel.cb)

        iscoroutinefunction.assert_called_with(
            unittest.mock.sentinel.cb,
        )


class Testoutbound_message_filter(unittest.TestCase):
    def setUp(self):
        self.decorator = service.outbound_message_filter

    def tearDown(self):
        del self.decorator

    def test_works_as_decorator(self):
        def cb():
            pass

        self.assertIs(
            cb,
            self.decorator(cb),
        )

    def test_adds_magic_attribute(self):
        def cb():
            pass

        self.decorator(cb)

        self.assertTrue(hasattr(cb, "_aioxmpp_service_handlers"))

    def test_adds__apply_outbound_message_filter_entry(self):
        def cb():
            pass

        self.decorator(cb)

        self.assertIn(
            service.HandlerSpec(
                (service._apply_outbound_message_filter, ()),
                is_unique=True,
                require_deps=(),
            ),
            cb._aioxmpp_service_handlers
        )

    def test_stacks_with_other_effects(self):
        def cb():
            pass

        cb._aioxmpp_service_handlers = {"foo"}

        self.decorator(cb)

        self.assertIn(
            service.HandlerSpec(
                (service._apply_outbound_message_filter, ()),
                is_unique=True,
                require_deps=(),
            ),
            cb._aioxmpp_service_handlers
        )

        self.assertIn(
            "foo",
            cb._aioxmpp_service_handlers,
        )

    def test_requires_non_coroutine(self):
        with unittest.mock.patch(
                "asyncio.iscoroutinefunction") as iscoroutinefunction:
            iscoroutinefunction.return_value = True

            with self.assertRaisesRegex(
                    TypeError,
                    "must not be a coroutine function"):
                self.decorator(unittest.mock.sentinel.cb)

        iscoroutinefunction.assert_called_with(
            unittest.mock.sentinel.cb,
        )


class Testoutbound_presence_filter(unittest.TestCase):
    def setUp(self):
        self.decorator = service.outbound_presence_filter

    def tearDown(self):
        del self.decorator

    def test_works_as_decorator(self):
        def cb():
            pass

        self.assertIs(
            cb,
            self.decorator(cb),
        )

    def test_adds_magic_attribute(self):
        def cb():
            pass

        self.decorator(cb)

        self.assertTrue(hasattr(cb, "_aioxmpp_service_handlers"))

    def test_adds__apply_outbound_presence_filter_entry(self):
        def cb():
            pass

        self.decorator(cb)

        self.assertIn(
            service.HandlerSpec(
                (service._apply_outbound_presence_filter, ()),
                is_unique=True,
                require_deps=(),
            ),
            cb._aioxmpp_service_handlers
        )

    def test_stacks_with_other_effects(self):
        def cb():
            pass

        cb._aioxmpp_service_handlers = {"foo"}

        self.decorator(cb)

        self.assertIn(
            service.HandlerSpec(
                (service._apply_outbound_presence_filter, ()),
                is_unique=True,
                require_deps=(),
            ),
            cb._aioxmpp_service_handlers
        )

        self.assertIn(
            "foo",
            cb._aioxmpp_service_handlers,
        )

    def test_requires_non_coroutine(self):
        with unittest.mock.patch(
                "asyncio.iscoroutinefunction") as iscoroutinefunction:
            iscoroutinefunction.return_value = True

            with self.assertRaisesRegex(
                    TypeError,
                    "must not be a coroutine function"):
                self.decorator(unittest.mock.sentinel.cb)

        iscoroutinefunction.assert_called_with(
            unittest.mock.sentinel.cb,
        )


class Testdepsignal(unittest.TestCase):
    class S1(service.Service):
        signal = callbacks.Signal()
        sync = callbacks.SyncSignal()

    def setUp(self):
        self.decorator = service.depsignal(
            self.S1,
            "signal",
        )

    def tearDown(self):
        del self.decorator

    def test_adds_magic_attribute(self):
        def cb():
            pass

        self.decorator(cb)

        self.assertTrue(hasattr(cb, "_aioxmpp_service_handlers"))

    def test_uses_strong_by_default(self):
        def cb():
            pass

        self.decorator(cb)

        self.assertIn(
            service.HandlerSpec(
                (
                    service._apply_connect_depsignal,
                    (
                        self.S1,
                        "signal",
                        callbacks.AdHocSignal.STRONG,
                    )
                ),
                is_unique=True,
                require_deps=(self.S1,),
            ),
            cb._aioxmpp_service_handlers
        )

    def test_defer_flag(self):
        self.decorator = service.depsignal(
            self.S1,
            "signal",
            defer=True,
        )

        def cb():
            pass

        with unittest.mock.patch.object(
                callbacks.AdHocSignal,
                "ASYNC_WITH_LOOP") as ASYNC_WITH_LOOP:
            ASYNC_WITH_LOOP.return_value = \
                unittest.mock.sentinel.async_with_loop
            self.decorator(cb)

        ASYNC_WITH_LOOP.assert_called_with(
            None,
        )

        self.assertIn(
            service.HandlerSpec(
                (
                    service._apply_connect_depsignal,
                    (
                        self.S1,
                        "signal",
                        unittest.mock.sentinel.async_with_loop,
                    )
                ),
                is_unique=True,
                require_deps=(self.S1,),
            ),
            cb._aioxmpp_service_handlers
        )

    def test_require_coroutinefunction_for_sync_signal(self):
        def cb():
            pass

        self.decorator = service.depsignal(
            self.S1,
            "sync",
        )

        with self.assertRaisesRegex(
                TypeError,
                "a coroutine function is required for this signal"):
            self.decorator(cb)

    def test_coroutinefunction_and_sync_signal(self):
        @asyncio.coroutine
        def coro():
            pass

        self.decorator = service.depsignal(
            self.S1,
            "sync",
        )

        self.decorator(coro)

        self.assertIn(
            service.HandlerSpec(
                (
                    service._apply_connect_depsignal,
                    (
                        self.S1,
                        "sync",
                        None,
                    )
                ),
                is_unique=True,
                require_deps=(self.S1,),
            ),
            coro._aioxmpp_service_handlers
        )

    def test_use_spawn_for_coroutinefunction_on_normal_signal_and_defer(self):
        self.decorator = service.depsignal(
            self.S1,
            "signal",
            defer=True,
        )

        @asyncio.coroutine
        def coro():
            pass

        with unittest.mock.patch.object(
                callbacks.AdHocSignal,
                "SPAWN_WITH_LOOP") as SPAWN_WITH_LOOP:
            SPAWN_WITH_LOOP.return_value = \
                unittest.mock.sentinel.spawn_with_loop
            self.decorator(coro)

        SPAWN_WITH_LOOP.assert_called_with(
            None,
        )

        self.assertIn(
            service.HandlerSpec(
                (
                    service._apply_connect_depsignal,
                    (
                        self.S1,
                        "signal",
                        unittest.mock.sentinel.spawn_with_loop,
                    )
                ),
                is_unique=True,
                require_deps=(self.S1,),
            ),
            coro._aioxmpp_service_handlers
        )

    def test_reject_coroutinefunction_on_normal_signal_without_defer(self):
        self.decorator = service.depsignal(
            self.S1,
            "signal",
        )

        @asyncio.coroutine
        def coro():
            pass

        with self.assertRaisesRegex(
                TypeError,
                "cannot use coroutine function with this signal "
                "without defer"):
            self.decorator(coro)

    def test_reject_defer_on_sync_signal(self):
        self.decorator = service.depsignal(
            self.S1,
            "sync",
            defer=True,
        )

        @asyncio.coroutine
        def coro():
            pass

        with self.assertRaisesRegex(
                ValueError,
                "cannot use defer with this signal"):
            self.decorator(coro)

    def test_stacks_with_other_effects(self):
        def cb():
            pass

        cb._aioxmpp_service_handlers = {"foo"}

        self.decorator(cb)

        self.assertIn(
            service.HandlerSpec(
                (
                    service._apply_connect_depsignal,
                    (
                        self.S1,
                        "signal",
                        callbacks.AdHocSignal.STRONG,
                    ),
                ),
                is_unique=True,
                require_deps=(self.S1,),
            ),
            cb._aioxmpp_service_handlers
        )

        self.assertIn(
            "foo",
            cb._aioxmpp_service_handlers,
        )

    def test_works_with_is_depsignal_handler(self):
        pass


class Testis_iq_handler(unittest.TestCase):
    def test_return_false_if_magic_attr_is_missing(self):
        self.assertFalse(
            service.is_iq_handler(
                unittest.mock.sentinel.type_,
                unittest.mock.sentinel.payload_cls,
                object()
            )
        )

    def test_return_true_if_token_in_magic_attr(self):
        m = unittest.mock.Mock()
        m._aioxmpp_service_handlers = [
            service.HandlerSpec(
                (service._apply_iq_handler,
                 (unittest.mock.sentinel.type_,
                  unittest.mock.sentinel.payload_cls)),
            )
        ]

        self.assertTrue(
            service.is_iq_handler(
                unittest.mock.sentinel.type_,
                unittest.mock.sentinel.payload_cls,
                m
            )
        )

    def test_return_false_if_token_not_in_magic_attr(self):
        m = unittest.mock.Mock()
        m._aioxmpp_service_handlers = [
            service.HandlerSpec(
                (service._apply_iq_handler,
                 (unittest.mock.sentinel.type2,
                  unittest.mock.sentinel.payload_cls2)),
            )
        ]

        self.assertFalse(
            service.is_iq_handler(
                unittest.mock.sentinel.type_,
                unittest.mock.sentinel.payload_cls,
                m
            )
        )


class Testis_message_handler(unittest.TestCase):
    def test_return_false_if_magic_attr_is_missing(self):
        self.assertFalse(
            service.is_message_handler(
                unittest.mock.sentinel.type_,
                unittest.mock.sentinel.from_,
                object()
            )
        )

    def test_return_true_if_token_in_magic_attr(self):
        m = unittest.mock.Mock()
        m._aioxmpp_service_handlers = [
            service.HandlerSpec(
                (service._apply_message_handler,
                    (unittest.mock.sentinel.type_,
                     unittest.mock.sentinel.from_))
            ),
        ]

        self.assertTrue(
            service.is_message_handler(
                unittest.mock.sentinel.type_,
                unittest.mock.sentinel.from_,
                m
            )
        )

    def test_return_false_if_token_not_in_magic_attr(self):
        m = unittest.mock.Mock()
        m._aioxmpp_service_handlers = [
            service.HandlerSpec(
                (service._apply_message_handler,
                 (unittest.mock.sentinel.type2,
                     unittest.mock.sentinel.from2))
            )
        ]

        self.assertFalse(
            service.is_message_handler(
                unittest.mock.sentinel.type_,
                unittest.mock.sentinel.from_,
                m
            )
        )


class Testis_presence_handler(unittest.TestCase):
    def test_return_false_if_magic_attr_is_missing(self):
        self.assertFalse(
            service.is_presence_handler(
                unittest.mock.sentinel.type_,
                unittest.mock.sentinel.from_,
                object()
            )
        )

    def test_return_true_if_token_in_magic_attr(self):
        m = unittest.mock.Mock()
        m._aioxmpp_service_handlers = [
            service.HandlerSpec(
                (service._apply_presence_handler,
                 (unittest.mock.sentinel.type_,
                  unittest.mock.sentinel.from_))
            )
        ]

        self.assertTrue(
            service.is_presence_handler(
                unittest.mock.sentinel.type_,
                unittest.mock.sentinel.from_,
                m
            )
        )

    def test_return_false_if_token_not_in_magic_attr(self):
        m = unittest.mock.Mock()
        m._aioxmpp_service_handlers = [
            service.HandlerSpec(
                (service._apply_presence_handler,
                 (unittest.mock.sentinel.type2,
                  unittest.mock.sentinel.from2))
            )
        ]

        self.assertFalse(
            service.is_presence_handler(
                unittest.mock.sentinel.type_,
                unittest.mock.sentinel.from_,
                m
            )
        )


class Testis_inbound_message_filter(unittest.TestCase):
    def test_return_false_if_magic_attr_is_missing(self):
        self.assertFalse(
            service.is_inbound_message_filter(
                object()
            )
        )

    def test_return_true_if_token_in_magic_attr(self):
        m = unittest.mock.Mock()
        m._aioxmpp_service_handlers = [
            service.HandlerSpec(
                (service._apply_inbound_message_filter,
                 ())
            )
        ]

        self.assertTrue(
            service.is_inbound_message_filter(m)
        )

    def test_return_false_if_token_not_in_magic_attr(self):
        m = unittest.mock.Mock()
        m._aioxmpp_service_handlers = [
            service.HandlerSpec(
                (service._apply_inbound_presence_filter,
                 ())
            )
        ]

        self.assertFalse(
            service.is_inbound_message_filter(m)
        )


class Testis_inbound_presence_filter(unittest.TestCase):
    def test_return_false_if_magic_attr_is_missing(self):
        self.assertFalse(
            service.is_inbound_presence_filter(
                object()
            )
        )

    def test_return_true_if_token_in_magic_attr(self):
        m = unittest.mock.Mock()
        m._aioxmpp_service_handlers = [
            service.HandlerSpec(
                (service._apply_inbound_presence_filter,
                 ())
            )
        ]

        self.assertTrue(
            service.is_inbound_presence_filter(m)
        )

    def test_return_false_if_token_not_in_magic_attr(self):
        m = unittest.mock.Mock()
        m._aioxmpp_service_handlers = [
            service.HandlerSpec(
                (service._apply_inbound_message_filter,
                 ())
            )
        ]

        self.assertFalse(
            service.is_inbound_presence_filter(m)
        )


class Testis_outbound_message_filter(unittest.TestCase):
    def test_return_false_if_magic_attr_is_missing(self):
        self.assertFalse(
            service.is_outbound_message_filter(
                object()
            )
        )

    def test_return_true_if_token_in_magic_attr(self):
        m = unittest.mock.Mock()
        m._aioxmpp_service_handlers = [
            service.HandlerSpec(
                (service._apply_outbound_message_filter,
                 ())
            )
        ]

        self.assertTrue(
            service.is_outbound_message_filter(m)
        )

    def test_return_false_if_token_not_in_magic_attr(self):
        m = unittest.mock.Mock()
        m._aioxmpp_service_handlers = [
            service.HandlerSpec(
                (service._apply_outbound_presence_filter,
                 ())
            )
        ]

        self.assertFalse(
            service.is_outbound_message_filter(m)
        )


class Testis_outbound_presence_filter(unittest.TestCase):
    def test_return_false_if_magic_attr_is_missing(self):
        self.assertFalse(
            service.is_outbound_presence_filter(
                object()
            )
        )

    def test_return_true_if_token_in_magic_attr(self):
        m = unittest.mock.Mock()
        m._aioxmpp_service_handlers = [
            service.HandlerSpec(
                (service._apply_outbound_presence_filter,
                 ())
            )
        ]

        self.assertTrue(
            service.is_outbound_presence_filter(m)
        )

    def test_return_false_if_token_not_in_magic_attr(self):
        m = unittest.mock.Mock()
        m._aioxmpp_service_handlers = [
            service.HandlerSpec(
                (service._apply_outbound_message_filter,
                 ())
            )
        ]

        self.assertFalse(
            service.is_outbound_presence_filter(m)
        )


class Testis_depsignal_handler(unittest.TestCase):
    class S1(service.Service):
        signal = callbacks.Signal()
        sync = callbacks.SyncSignal()

    def test_return_false_if_magic_attr_is_missing(self):
        self.assertFalse(
            service.is_depsignal_handler(
                self.S1,
                "signal",
                object(),
            )
        )

    def test_return_true_if_token_in_magic_attr(self):
        def cb(self):
            pass

        @asyncio.coroutine
        def coro(self):
            pass

        tokens = [
            (
                "signal",
                False,
                cb,
                service.HandlerSpec(
                    (
                        service._apply_connect_depsignal,
                        (
                            self.S1,
                            "signal",
                            callbacks.AdHocSignal.STRONG,
                        ),
                    ),
                    require_deps=(self.S1,)
                )
            ),
            (
                "signal",
                True,
                cb,
                service.HandlerSpec(
                    (
                        service._apply_connect_depsignal,
                        (
                            self.S1,
                            "signal",
                            unittest.mock.sentinel.async_with_loop,
                        ),
                    ),
                    require_deps=(self.S1,)
                )
            ),
            (
                "signal",
                True,
                coro,
                service.HandlerSpec(
                    (
                        service._apply_connect_depsignal,
                        (
                            self.S1,
                            "signal",
                            unittest.mock.sentinel.spawn_with_loop,
                        ),
                    ),
                    require_deps=(self.S1,)
                )
            ),
            (
                "sync",
                False,
                coro,
                service.HandlerSpec(
                    (
                        service._apply_connect_depsignal,
                        (
                            self.S1,
                            "sync",
                            None,
                        ),
                    ),
                    require_deps=(self.S1,),
                )
            ),
        ]

        for signal_name, defer, obj, spec in tokens:
            with contextlib.ExitStack() as stack:
                SPAWN_WITH_LOOP = stack.enter_context(
                    unittest.mock.patch.object(
                        callbacks.AdHocSignal,
                        "SPAWN_WITH_LOOP")
                )
                SPAWN_WITH_LOOP.return_value = \
                    unittest.mock.sentinel.spawn_with_loop

                ASYNC_WITH_LOOP = stack.enter_context(
                    unittest.mock.patch.object(
                        callbacks.AdHocSignal,
                        "ASYNC_WITH_LOOP")
                )
                ASYNC_WITH_LOOP.return_value = \
                    unittest.mock.sentinel.async_with_loop

                obj._aioxmpp_service_handlers = [
                    spec,
                ]

                self.assertTrue(
                    service.is_depsignal_handler(
                        self.S1,
                        signal_name,
                        obj,
                        defer=defer,
                    ),
                    spec,
                )

    def test_return_false_if_token_not_in_magic_attr(self):
        m = unittest.mock.Mock()
        m._aioxmpp_service_handlers = [
            service.HandlerSpec(
                (service._apply_outbound_message_filter,
                 ())
            )
        ]

        self.assertFalse(
            service.is_depsignal_handler(
                self.S1,
                "signal",
                m,
                defer=True,
            )
        )


class TestDescriptor(unittest.TestCase):
    class DescriptorSubclass(service.Descriptor):
        def init_cm(self, instance):
            return unittest.mock.sentinel.cm

    def setUp(self):
        self.d = self.DescriptorSubclass()

    def tearDown(self):
        del self.d

    def test_is_abstract_class(self):
        with self.assertRaisesRegex(TypeError, "abstract methods init_cm"):
            service.Descriptor()

    def test_add_to_stack_uses_init_cm_to_obtain_cm_and_pushes(self):
        with contextlib.ExitStack() as stack:
            init_cm = stack.enter_context(
                unittest.mock.patch.object(self.d, "init_cm")
            )
            init_cm.return_value = unittest.mock.sentinel.cm

            target_stack = unittest.mock.Mock()

            result = self.d.add_to_stack(
                unittest.mock.sentinel.instance,
                target_stack,
            )

        init_cm.assert_called_once_with(
            unittest.mock.sentinel.instance,
        )

        target_stack.enter_context.assert_called_once_with(
            unittest.mock.sentinel.cm,
        )

        self.assertEqual(
            result,
            target_stack.enter_context(),
        )

    def test___get___returns_self_for_None_instance(self):
        self.assertIs(
            self.d.__get__(None, unittest.mock.sentinel.owner),
            self.d,
        )

    def test___get___raises_AttributeError_if_not_initialised(self):
        with self.assertRaisesRegex(
                AttributeError,
                r"resource manager descriptor has not been initialised"):
            self.d.__get__(
                unittest.mock.sentinel.instance,
                unittest.mock.sentinel.owner
            )

    def test_add_to_stack_causes___get___to_return_the_cm_result(self):
        target_stack = unittest.mock.Mock()

        result1 = self.d.add_to_stack(
            unittest.mock.sentinel.instance,
            target_stack,
        )

        result2 = self.d.__get__(
            unittest.mock.sentinel.instance,
            unittest.mock.sentinel.owner,
        )

        self.assertEqual(result1, result2)

    def test___get___works_with_different_instances(self):
        target_stack = unittest.mock.Mock()

        result11 = self.d.add_to_stack(
            unittest.mock.sentinel.instance1,
            target_stack,
        )

        result12 = self.d.add_to_stack(
            unittest.mock.sentinel.instance2,
            target_stack,
        )

        result21 = self.d.__get__(
            unittest.mock.sentinel.instance1,
            unittest.mock.sentinel.owner,
        )

        result22 = self.d.__get__(
            unittest.mock.sentinel.instance2,
            unittest.mock.sentinel.owner,
        )

        with self.assertRaises(AttributeError):
            self.d.__get__(
                unittest.mock.sentinel.instance3,
                unittest.mock.sentinel.owner,
            )

        self.assertEqual(result11, result21)
        self.assertEqual(result12, result22)

    def test_add_to_stack_stores_with_weakref(self):
        with contextlib.ExitStack() as stack:
            WeakKeyDictionary = stack.enter_context(
                unittest.mock.patch(
                    "weakref.WeakKeyDictionary",
                    new=unittest.mock.MagicMock(),
                ),
            )

            target_stack = unittest.mock.Mock()

            self.d = self.DescriptorSubclass()

            WeakKeyDictionary.assert_called_once_with()

            self.d.add_to_stack(
                unittest.mock.sentinel.instance,
                target_stack,
            )

            self.assertIn(
                unittest.mock._Call((
                    "__setitem__",
                    (
                        unittest.mock.sentinel.instance,
                        (
                            unittest.mock.sentinel.cm,
                            target_stack.enter_context(),
                        )
                    ),
                    {}
                )),
                WeakKeyDictionary().mock_calls,
            )

.. _changelog:

Changelog
#########

Version 0.8
===========

* Context managers :func:`aioxmpp.stream.iq_handler`,
  :func:`aioxmpp.stream.message_handler`,
  :func:`aioxmpp.stream.presence_handler`, and
  :func:`aioxmpp.stream.stanza_filter`.

* :ref:`api-aioxmpp.service-decorators` for :class:`aioxmpp.service.Service`
  methods.

* :attr:`aioxmpp.service.Service.dependencies`

* Ported existing service subclasses to decorators.

* :meth:`aioxmpp.muc.Room.request_voice`

* Fix resource leak which would emit::

    task: <Task pending coro=<OrderedStateMachine.wait_for() running at /home/horazont/Projects/python/aioxmpp/aioxmpp/statemachine.py:170> wait_for=<Future pending cb=[Task._wakeup()]> cb=[XMLStream._stream_starts_closing()]>

* Support for ANONYMOUS SASL mechanism. See :meth:`aioxmpp.security_layer.make`
  for details.

* **Breaking change:** If any of the connection errors encountered in
  :meth:`aioxmpp.node.connect_xmlstream` is a :class:`aioxmpp.errors.TLSFailure`
  *and all* other connection options also failed, the
  :class:`~.errors.TLSFailure` is re-raised instead of a
  :class:`aioxmpp.errors.MultiOSError` instance. This helps to prevent masking
  of configuration problems.

* **Breaking change:** The handling of connection errors in
  :class:`~.node.AbstractClient` has been modified:

  * The change of :meth:`aioxmpp.node.connect_xmlstream` described above also
    affects the behaviour of the node, as :class:`~.errors.TLSFailure` errors
    are treated as critical (in contrast to :class:`OSError` subclasses).

  * The number of connection attempts made before the first connection is
    successful is now bounded, configurable through the new parameter
    `max_initial_attempts`. The default is at 4, which gives (together with the
    default exponential backoff parameters) a minimum time of attempted
    connections of about 5 seconds.

  * :meth:`~.AbstractClient.on_stream_suspended` was added (this is not a
    breaking change)

  * :meth:`~.AbstractClient.on_stream_destroyed` got a new argument `reason`
    which gives the exception which caused the stream to be destroyed.

* Improve compatibility of :mod:`aioxmpp.muc` with Prosody 0.9 and below, which
  misses sending the ``110`` status code on some presences.

* Fix :meth:`aioxmpp.muc.Room.leave_and_wait` never returning.

* Do not emit :meth:`aioxmpp.muc.Room.on_join` when an unavailable presence from
  an unknown occupant JID is received.

* :mod:`aioxmpp.e2etest`: Framework for End-to-End/Integration tests.

* Get rid of dependency on libxml2 development files. libxml2 itself is still
  required, both directly and indirectly (through the lxml dependency).

* *Deprecation*: Rename several services:

  * :class:`aioxmpp.shim.Service` -> :class:`aioxmpp.SHIMService`
  * :class:`aioxmpp.muc.Service` -> :class:`aioxmpp.MUCClient`
  * :class:`aioxmpp.presence.Service` -> :class:`aioxmpp.PresenceClient`
  * :class:`aioxmpp.roster.Service` -> :class:`aioxmpp.RosterClient`
  * :class:`aioxmpp.entitycaps.Service` -> :class:`aioxmpp.EntityCapsService`

  The old names are still available until 1.0.

* *Possibly breaking change*: :class:`aioxmpp.disco.Service` was split into
  :class:`aioxmpp.DiscoClient` and :class:`aioxmpp.DiscoServer`.

* :class:`aioxmpp.stream.StanzaToken` objects are now :term:`awaitable`.

* :meth:`aioxmpp.stream.StanzaStream.send`

* *Deprecation*: :meth:`aioxmpp.stream.StanzaStream.send_and_wait_for_sent`
  deprecated in favour of :meth:`~.StanzaStream.send`.

* *Deprecation*: :meth:`aioxmpp.stream.StanzaStream.send_iq_and_wait_for_reply`
  deprecated in favour of :meth:`~.StanzaStream.send`.

* *Deprecation*: :meth:`aioxmpp.stream.StanzaStream.enqueue_stanza` is now
  called :meth:`~aioxmpp.stream.StanzaStream.enqueue`.

* :class:`aioxmpp.PresenceServer`

* Fix :exc:`AttributeError` being raised from ``state > None`` (and other
  comparison operators), with ``state`` being a :class:`aioxmpp.PresenceState`
  instance.

  The more correct :exc:`TypeError` is now raised.

* *Deprecation*: The `presence` argument to the constructor of and the
  :attr:`~.UseConnected.presence` and :attr:`~.UseConnected.timeout` attributes
  on :class:`aioxmpp.node.UseConnected` objects are deprecated.

  See the respective documentation for details on the deprecation procedure.

.. _api-changelog-0.7:

Version 0.7
===========

* **License change**: As of version 0.7, :mod:`aioxmpp` is distributed under the
  terms of the GNU Lesser General Public License version 3 or later (LGPLv3+).
  The exact terms are, as usual, found by taking a look at ``COPYING.LESSER`` in
  the source code repository.

* New XEP implementations:

  * :mod:`aioxmpp.forms` (:xep:`4`): An implementation of the Data Forms XEP.
    Take a look and see where it gets you.

* New features in the :mod:`aioxmpp.xso` submodule:

  * The new :class:`aioxmpp.xso.ChildFlag` descriptor is a simplification of the
    :class:`aioxmpp.xso.ChildTag`. It can be used where the presence or absence of
    a child element *only* signals a boolean flag.

  * The new :class:`aioxmpp.xso.EnumType` type allows using a :mod:`enum`
    enumeration as XSO descriptor type.

* Often-used names have now been moved to the :mod:`aioxmpp` namespace:

  * The stanza classes :class:`aioxmpp.IQ`, :class:`aioxmpp.Message`,
    :class:`aioxmpp.Presence`
  * The type enumerations (see below) :class:`aioxmpp.IQType`,
    :class:`aioxmpp.MessageType`, :class:`aioxmpp.PresenceType`
  * Commonly used structures: :class:`aioxmpp.JID`,
    :class:`aioxmpp.PresenceState`
  * Exceptions: :class:`aioxmpp.XMPPCancelError` and its buddies

* **Horribly Breaking Change** in the future: :attr:`aioxmpp.IQ.type_`,
  :attr:`aioxmpp.Message.type_`, :attr:`aioxmpp.Presence.type_`
  and :attr:`aioxmpp.stanza.Error.type_` now use :class:`aioxmpp.xso.EnumType`,
  with corresponding enumerations (see docs of the respective attributes).

  This will break about every piece of code ever written for aioxmpp, and it is
  not trivial to fix automatically. This is why the following fallbacks have
  been implemented:

  1. The :attr:`type_` attributes still accept their string (or :data:`None` in
     the case of :attr:`.Presence.type_`) values when being written. When being
     read, the attributes always return the actual enumeration value.

  2. The relevant enumeration members compare equal (and hash equally) to their
     values. Thus, ``MessageType.CHAT == "chat"`` is still true (and
     ``MessageType.CHAT != "chat"`` is false).

  3. :meth:`~.StanzaStream.register_message_callback`,
     :meth:`~.StanzaStream.register_presence_callback`, and
     :meth:`~.StanzaStream.register_iq_request_coro`, as well as their
     corresponding un-registration methods, all accept the string variants for
     their arguments, internally mapping them to the actual enumeration values.

  .. note::

     As a matter of fact (good news!), with only the fallbacks and no code
     fixes, the :mod:`aioxmpp` test suite passes. So it is likely that you will
     not notice any breakage in the 0.7 release, giving you quite some time to
     react.

  These fallbacks will be *removed* with aioxmpp 1.0, making the legacy use
  raise :exc:`TypeError` or fail silently. Each of these fallbacks currently
  produces a :exc:`DeprecationWarning`.

  .. note::

     :exc:`DeprecationWarning` warnings are not shown by default in Python 3. To
     enable them, either run the interpreter with the ``-Wd`` option, un-filter
     them explicitly using ``warnings.simplefilter("always")`` at the top of
     your program, or explore other options as documented in :mod:`warnings`.

  So, now I said I will be breaking all your code, how do you fix it? There are
  two ways to find affected pieces of code: (1) run it with warnings (see
  above), which will find all affected pieces of code and (2) use the shell
  script provided at `utils/find-v0.7-type-transitions.sh
  <https://github.com/horazont/aioxmpp/blob/devel/utils/find-v0.7-type-transitions.sh>`_
  to find a subset of potentially affected pieces of code automatically. The
  shell script uses `The Silver Searcher (ag) <http://geoff.greer.fm/ag/>`_
  (find it in your distributions package repositories, I know it is there on
  Fedora, Arch and Debian!) and regular expressions to find common patterns.
  Example usage::

    # find everything in the current subdirectory
    $ $AIOXMPPPATH/utils/find-v0.7-type-transitions.sh
    # only search in the foobar/ subdirectory
    $ $AIOXMPPPATH/utils/find-v0.7-type-transitions.sh foobar/
    # only look at the foobar/baz.py file
    $ $AIOXMPPPATH/utils/find-v0.7-type-transitions.sh foobar/baz.py

  The script was built while fixing :mod:`aioxmpp` itself after the bug. It has
  not found *all* affected pieces of code, but the vast majority. The others can
  be found by inspecting :exc:`DeprecationWarning` warnings being emitted.

* The :func:`aioxmpp.security_layer.make` makes creating a security layer much
  less cumbersome than before. It provides a simple interface supporting
  password authentication, certificate pinning and others.

  The interface of this function will be extended in the future when more
  authentication or certificate verification mechanisms come around.

* The two methods :meth:`aioxmpp.muc.Service.get_room_config`,
  :meth:`aioxmpp.muc.Service.set_room_config` have been implemented, allowing to
  manage MUC room configurations.

* Fix bug in :meth:`aioxmpp.xso.ChildValueMultiMap.to_sax` which rendered XSOs
  with that descriptor useless.

* Fix documentation on :meth:`aioxmpp.PresenceManagedClient.set_presence`.

* :class:`aioxmpp.callbacks.AdHocSignal` now logs when coroutines registered
  with :meth:`aioxmpp.callbacks.AdHocSignal.SPAWN_WITH_LOOP` raise exceptions or
  return non-:data:`None` values. See the documentation of
  :meth:`~aioxmpp.callbacks.AdHocSignal.SPAWN_WITH_LOOP` for details.

* :func:`aioxmpp.pubsub.xso.as_payload_class` is a decorator (akin to
  :meth:`aioxmpp.IQ.as_payload_class`) to declare that your
  :class:`~aioxmpp.xso.XSO` shall be allowed as pubsub payload.

* :meth:`~.StanzaStream.register_message_callback` and
  :meth:`~.StanzaStream.register_presence_callback` now explicitly raise
  :class:`ValueError` when an attempt to overwrite an existing listener is made,
  instead of silently replacing the callback.

Version 0.6
===========

* New dependencies:

  * :mod:`multidict` from :mod:`aiohttp`.
  * :mod:`aioopenssl`: This is the former :mod:`aioxmpp.ssl_transport` as a
    separate package; :mod:`aioxmpp` still ships with a fallback in case that
    package is not installed.

* New XEP implementations:

  * partial :mod:`aioxmpp.pubsub` (:xep:`60`): Everything which requires forms
    is not implemented yet. Publish/Subscribe/Retract and creation/deletion of
    nodes is verified to work (against `Prosody <https://prosody.im>`_ at
    least).

  * :mod:`aioxmpp.shim` (:xep:`131`), used for :mod:`aioxmpp.pubsub`.

  * :xep:`368` support was added.

* New features in the :mod:`aioxmpp.xso` subpackage:

  * :class:`aioxmpp.xso.NumericRange` validator, which can be used to validate
    the range of any orderable type.

  * :mod:`aioxmpp.xso.query`, a module which allows for running queries against
    XSOs. This is still highly experimental.

  * :class:`aioxmpp.xso.ChildValueMultiMap` descriptor, which uses
    :mod:`multidict` and is used in :mod:`aioxmpp.shim`.

* :mod:`aioxmpp.network` was rewritten for 0.5.4

  The control over the used DNS resolver is now more sophisticated. Most
  notably, :mod:`aioxmpp.network` uses a thread-local resolver which is used for
  all queries by default.

  Normally, :func:`aioxmpp.network.repeated_query` will now re-configure the
  resolver from system-wide resolver configuration after the first timeout
  occurs.

  The resolver can be overridden (disabling the reconfiguration magic) using
  :func:`aioxmpp.network.set_resolver`.

* **Breaking change:** :class:`aioxmpp.service.Service` does not accept a
  `logger` argument anymore; instead, it now accepts a `base_logger` argument.
  Refer to the documentation of the class for details.

  The `base_logger` is automatically passed by
  :meth:`aioxmpp.node.AbstractClient.summon` on construction of the service and
  is the :attr:`aioxmpp.node.AbstractClient.logger` of the client instance.

* **Breaking change:** :class:`aioxmpp.xso.XSO` subclasses (or more
  specifically, instances of the :class:`aioxmpp.xso.model.XMLStreamClass`
  metaclass) now automatically declare a :attr:`__slots__` attribute.

  The mechanics are documented in detail on
  :attr:`aioxmpp.xso.model.XMLStreamClass.__slots__`.

* **Breaking change:** The following functions have been removed:

  * :func:`aioxmpp.node.connect_to_xmpp_server`
  * :func:`aioxmpp.node.connect_secured_xmlstream`
  * :func:`aioxmpp.security_layer.negotiate_stream_security`

  Use :func:`aioxmpp.node.connect_xmlstream` instead, but check the docs for the
  slightly different semantics.

  The following functions have been deprecated:

  * :class:`aioxmpp.security_layer.STARTTLSProvider`
  * :func:`aioxmpp.security_layer.security_layer`

  Use :class:`aioxmpp.security_layer.SecurityLayer` instead.

  The existing helper function
  :func:`aioxmpp.security_layer.tls_with_password_based_authentication` is still
  live and has been modified to use the new code.

* *Possibly breaking change:* The arguments to
  :meth:`aioxmpp.CertificateVerifier.pre_handshake` are now completely
  different. But as this method is not documented, this should not be a problem.

* *Possibly breaking change:* Attributes starting with ``_xso_`` are now also
  reserved on subclasses of :class:`aioxmpp.xso.XSO` (together with the
  long-standing reservation of attributes starting with ``xso_``).

* :meth:`aioxmpp.stanza.Error.as_application_condition`
* :meth:`aioxmpp.stanza.make_application_error`

* Several bugfixes in :mod:`aioxmpp.muc`:

  * :meth:`aioxmpp.muc.Room.on_message` now receives a proper `occupant` argument
    if occupant data is available when the message is received.

  * MUCs now autorejoin correctly after a disconnect.

  * Fix crash when using :class:`aioxmpp.tracking.MessageTracker` (e.g.
    indirectly through :meth:`aioxmpp.muc.Room.send_tracked_message`).

    Thanks to `@gudvnir <https://github.com/gudvinr>`_ over at github for
    pointing this out (see `issue#7
    <https://github.com/horazont/aioxmpp/issues/7>`_).

* Several bugfixes related to :class:`aioxmpp.protocol.XMLStream`:

  * :mod:`asyncio` errors/warnings about pending tasks being destroyed after
    disconnects should be gone now (:class:`aioxmpp.protocol.XMLStream` now
    properly cleans up its running coroutines).

  * The :class:`aioxmpp.protocol.XMLStream` is now closed or aborted by the
    :class:`aioxmpp.stream.StanzaStream` if the stream fails. This prevents
    lingering half-open TCP streams.

    See :meth:`aioxmpp.stream.StanzaStream.on_failure` for details.

* Some behaviour changes in :class:`aioxmpp.stream.StanzaStream`:

  When the stream is stopped without SM enabled, the following new behaviour has
  been introduced:

  * :attr:`~aioxmpp.stream.StanzaState.ACTIVE` stanza tokens are set to
    :attr:`~aioxmpp.stream.StanzaState.DISCONNECTED` state.

  * Coroutines which were spawned due to them being registered with
    :meth:`~aioxmpp.stream.StanzaStream.register_iq_request_coro` are
    :meth:`asyncio.Task.cancel`\ -ed.

  The same as above holds if the stream is closed, even if SM is enabled (as
  stream closure is clean and will broadcast unavailable presence server-side).

  This provides more fail-safe behaviour while still providing enough feedback.

* New method: :meth:`aioxmpp.stream.StanzaStream.send_and_wait_for_sent`.
  :meth:`~aioxmpp.stream.StanzaStream.send_iq_and_wait_for_reply` now also uses
  this.

* New method :meth:`aioxmpp.PresenceManagedClient.connected` and new class
  :class:`aioxmpp.node.UseConnected`.

  The former uses the latter to provide an asynchronous context manager which
  starts and stops a :class:`aioxmpp.PresenceManagedClient`. Intended for
  use in situations where an XMPP client is needed in-line. It saves a lot of
  boiler plate by taking care of properly waiting for the connection to be
  established etc.

* Fixed incorrect documentation of :meth:`aioxmpp.disco.Service.query_info`.
  Previously, the docstring incorrectly claimed that the method would return the
  result of :meth:`aioxmpp.disco.xso.InfoQuery.to_dict`, while it would in fact
  return the :class:`aioxmpp.disco.xso.InfoQuery` instance.

* Added `strict` arguments to :class:`aioxmpp.JID`. See the class
  docmuentation for details.

* Added `strict` argument to :class:`aioxmpp.xso.JID` and made it non-strict by
  default. See the documentation for rationale and details.

* Improve robustness against erroneous and malicious stanzas.

  All parsing errors on stanzas are now caught and handled by
  :meth:`aioxmpp.stream._process_incoming_erroneous_stanza`, which at least logs
  the synopsis of the stanza as parsed. It also makes sure that stream
  management works correctly, even if some stanzas are not understood.

  Additionally, a bug in the :class:`aioxmpp.xml.XMPPXMLProcessor` has been
  fixed which prevented errors in text content from being caught.

* No visible side-effects: Replaced deprecated
  :meth:`unittest.TestCase.assertRaisesRegexp` with
  :meth:`unittest.TestCase.assertRaisesRegex` (`thanks, Maxim
  <https://github.com/horazont/aioxmpp/pull/5>`_).

* Fix generation of IDs when sending stanzas. It has been broken for anything
  but IQ stanzas for some time.

* Send SM acknowledgement when closing down stream. This prevents servers from
  sending error stanzas for the unacked stanzas ☺.

* New callback mode :meth:`aioxmpp.callbacks.AdHocSignal.SPAWN_WITH_LOOP`.

* :mod:`aioxmpp.connector` added. This module provides classes which connect and
  return a :class:`aioxmpp.protocol.XMLStream`. They also handle TLS
  negotiation, if any.

* :class:`aioxmpp.node.AbstractClient` now accepts an `override_peer` argument,
  which may be a sequence of connection options as returned by
  :func:`aioxmpp.node.discover_connectors`. See the class documentation for
  details.

Version 0.6.1
-------------

* Fix :exc:`TypeError` crashes when using :mod:`aioxmpp.entitycaps`,
  :mod:`aioxmpp.presence` or :mod:`aioxmpp.roster`, arising from the argument
  change to service classes.

Version 0.5
===========

* Support for :xep:`0045` multi-user chats is now available in the
  :mod:`aioxmpp.muc` subpackage.

* Mostly transparent support for :xep:`0115` (Entity Capabilities) is now
  available using the :mod:`aioxmpp.entitycaps` subpackage.

* Support for transparent non-scalar attributes, which get mapped to XSOs. Use
  cases are dicts mapping language tags to strings (such as for message
  ``body`` elements) or sets of values which are represented by discrete XML
  elements.

  For this, the method :meth:`~aioxmpp.xso.AbstractType.get_formatted_type` was
  added to :class:`aioxmpp.xso.AbstractType` and two new descriptors,
  :class:`aioxmpp.xso.ChildValueMap` and :class:`aioxmpp.xso.ChildValueList`,
  were implemented.

  .. autosummary::

     ~aioxmpp.xso.ChildValueMap
     ~aioxmpp.xso.ChildValueList
     ~aioxmpp.xso.ChildTextMap

  **Breaking change**: The above descriptors are now used at several places,
  breaking the way these attributes need to be accessed:

  * :attr:`aioxmpp.Message.subject`,
  * :attr:`aioxmpp.Message.body`,
  * :attr:`aioxmpp.Presence.status`,
  * :attr:`aioxmpp.disco.xso.InfoQuery.features`,
  * and possibly others.

* Several stability improvements have been made. A race condition during stream
  management resumption was fixed and :class:`aioxmpp.node.AbstractClient`
  instances now stop if non-:class:`OSError` exceptions emerge from the
  stream (as these usually indicate an implementation or user error).

  :class:`aioxmpp.callbacks.AdHocSignal` now provides full exception
  isolation.

* Support for capturing the raw XML events used for creating
  :class:`aioxmpp.xso.XSO` instances from SAX is now provided through
  :class:`aioxmpp.xso.CapturingXSO`. Helper functions to work with these events
  are also provided, most notably :func:`aioxmpp.xso.events_to_sax`, which can
  be used to re-create the original XML from those events.

  The main use case is to be able to write out a transcript of received XML
  data, independent of XSO-level understanding for the data received, provided
  the parts which are understood are semantically correct (transcripts will be
  incomplete if parsing fails due to incorrect contents).

  .. autosummary::

     ~aioxmpp.xso.CapturingXSO
     ~aioxmpp.xso.capture_events
     ~aioxmpp.xso.events_to_sax

  This feature is already used in :class:`aioxmpp.disco.xso.InfoQuery`, which
  now inherits from :class:`~aioxmpp.xso.CapturingXSO` and provides its
  transcript (if available) at
  :attr:`~aioxmpp.disco.xso.InfoQuery.captured_events`.

* The core SASL implementation has been refactored in its own independent
  package, :mod:`aiosasl`. Only the XMPP specific parts reside in
  :mod:`aioxmpp.sasl` and :mod:`aioxmpp` now depends on :mod:`aiosasl`.

* :meth:`aioxmpp.stream.StanzaStream.register_message_callback` is more clearly
  specified now, a bug in the documentation has been fixed.

* :mod:`aioxmpp.stream_xsos` is now called :mod:`aioxmpp.nonza`, in accordance
  with :xep:`0360`.

* :class:`aioxmpp.xso.Date` and :class:`aioxmpp.xso.Time` are now available to
  for :xep:`0082` use. In addition, support for the legacy date time format is
  now provided in :class:`aioxmpp.xso.DateTime`.

  .. autosummary::

     ~aioxmpp.xso.Date
     ~aioxmpp.xso.Time
     ~aioxmpp.xso.DateTime

* The Python 3.5 compatibility of the test suite has been improved. In a
  corner-case, :class:`StopIteration` was emitted from ``data_received``, which
  caused a test to fail with a :class:`RuntimeError` due to implementation of
  :pep:`0479` in Python 3.5. See the `issue at github
  <https://github.com/horazont/aioxmpp/issues/3>`_.

* Helper functions for reading and writing single XSOs (and their children) to
  binary file-like objects have been introduced.

  .. autosummary::

     ~aioxmpp.xml.write_single_xso
     ~aioxmpp.xml.read_xso
     ~aioxmpp.xml.read_single_xso

* In 0.5.4, :mod:`aioxmpp.network` was re-written. More details will follow in
  the 0.6 changelog. The takeaway is that the network stack now automatically
  reloads the DNS configuration after the first timeout, to accomodate to
  changing resolvers.

Version 0.4
===========

* Documentation change: A simple sphinx extension has been added which
  auto-detects coroutines and adds a directive to mark up signals.

  The latter has been added to relevant places and the former automatically
  improves the documentations quality.

* :class:`aioxmpp.roster.Service` now implements presence subscription
  management. To track the presence of peers, :mod:`aioxmpp.presence` has been
  added.

* :mod:`aioxmpp.stream` and :mod:`aioxmpp.nonza` are part of the public
  API now. :mod:`aioxmpp.nonza` has gained the XSOs for SASL (previously
  in :mod:`aioxmpp.sasl`) and StartTLS (previously in
  :mod:`aioxmpp.security_layer`).

* :class:`aioxmpp.xso.XSO` subclasses now support copying and deepcopying.

* :mod:`aioxmpp.protocol` has been moved into the internal API part.

* :class:`aioxmpp.Message` specification fixed to have
  ``"normal"`` as default for :attr:`~aioxmpp.Message.type_` and relax
  the unknown child policy.

* *Possibly breaking change*: :attr:`aioxmpp.xso.XSO.DECLARE_NS` is now
  automatically generated by the meta class
  :class:`aioxmpp.xso.model.XMLStreamClass`. See the documentation for the
  detailed rules.

  To get the old behaviour for your class, you have to put ``DECLARE_NS = {}``
  in its declaration.

* :class:`aioxmpp.stream.StanzaStream` has a positional, optional argument
  (`local_jid`) for ejabberd compatiblity.

* Several fixes and workarounds, finally providing ejabberd compatibility:

  * :class:`aioxmpp.nonza.StartTLS` declares its namespace
    prefixless. Otherwise, connections to some versions of ejabberd fail in a
    very humorous way: client says "I want to start TLS", server says "You have
    to use TLS" and closes the stream with a policy-violation stream error.

  * Most XSOs now declare their namespace prefixless, too.

  * Support for legacy (`RFC 3921`__) XMPP session negotiation implemented in
    :class:`aioxmpp.node.AbstractClient`. See :mod:`aioxmpp.rfc3921`.

    __ https://tools.ietf.org/html/rfc3921

  * :class:`aioxmpp.stream.StanzaStream` now supports incoming IQs with the
    bare JID of the local entity as sender, taking them as coming from the
    server.

* Allow pinning of certificates for which no issuer certificate is available,
  because it is missing in the server-provided chain and not available in the
  local certificate store. This is, with respect to trust, treated equivalent
  to a self-signed cert.

* Fix stream management state going out-of-sync when an erroneous stanza
  (unknown payload, type or validator errors on the payload) was received. In
  addition, IQ replies which cannot be processed raise
  :class:`aioxmpp.errors.ErroneousStanza` from
  :meth:`aioxmpp.stream.StanzaStream.send_iq_and_wait_for_reply` and when
  registering futures for the response using
  :meth:`aioxmpp.stream.StanzaStream.register_iq_response_future`. See the
  latter for details on the semantics.

* Fixed a bug in :class:`aioxmpp.xml.XMPPXMLGenerator` which would emit
  elements in the wrong namespace if the meaning of a XML namespace prefix was
  being changed at the same time an element was emitted using that namespace.

* The defaults for unknown child and attribute policies on
  :class:`aioxmpp.xso.XSO` are now ``DROP`` and not ``FAIL``. This is for
  better compatibility with old implementations and future features.

Version 0.3
===========

* **Breaking change**: The `required` keyword argument on most
  :mod:`aioxmpp.xso` descriptors has been removed. The semantics of the
  `default` keyword argument have been changed.

  Before 0.3, the XML elements represented by descriptors were not required by
  default and had to be marked as required e.g. by setting ``required=True`` in
  :class:`.xso.Attr` constructor.

  Since 0.3, the descriptors are generally required by default. However, the
  interface on how to change that is different. Attributes and text have a
  `default` keyword argument which may be set to a value (which may also be
  :data:`None`). In that case, that value indicates that the attribute or text
  is absent: it is used if the attribute or text is missing in the source XML
  and if the attribute or text is set to the `default` value, it will not be
  emitted in XML.

  Children do not support default values other than :data:`None`; thus, they
  are simply controlled by a boolean flag `required` which needs to be passed
  to the constructor.

* The class attributes :attr:`~aioxmpp.service.Meta.SERVICE_BEFORE` and
  :attr:`~aioxmpp.service.Meta.SERVICE_AFTER` have been
  renamed to :attr:`~aioxmpp.service.Meta.ORDER_BEFORE` and
  :attr:`~aioxmpp.service.Meta.ORDER_AFTER` respectively.

  The :class:`aioxmpp.service.Service` class has additional support to handle
  the old attributes, but will emit a DeprecationWarning if they are used on a
  class declaration.

  See :attr:`aioxmpp.service.Meta.SERVICE_AFTER` for more information on the
  deprecation cycle of these attributes.

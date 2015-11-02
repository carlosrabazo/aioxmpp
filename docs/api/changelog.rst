.. _changelog:

Changelog
#########

Version 0.4
===========

* Documentation change: A simple sphinx extension has been added which
  auto-detects coroutines and adds a directive to mark up signals.

  The latter has been added to relevant places and the former automatically
  improves the documentations quality.

* :class:`aioxmpp.roster.Service` now implements presence subscription
  management.

* :mod:`aioxmpp.stream` and :mod:`aioxmpp.stream_xsos` are part of the public
  API now.

* :class:`aioxmpp.xso.XSO` subclasses now support copying and deepcopying.

* :mod:`aioxmpp.presence` implemented.

* :mod:`aioxmpp.protocol` has been moved into the internal API part.

* :class:`aioxmpp.stanza.Message` specification fixed to have
  ``"normal"`` as default for :attr:`~aioxmpp.stanza.Message.type_` and relax
  the unknown child policy.

* Moved the XSO classes for Start TLS to :mod:`aioxmpp.stream_xsos`, where they
  belong.

* Make sure that :class:`aioxmpp.stream_xsos.StartTLS` declares a prefixless
  namespace---otherwise, connections to some versions of ejabberd fail in a
  very humorous way: client says "I want to start TLS", server says "You have
  to use TLS" and closes the stream with a policy-violation stream error.

* Allow pinning of certificates for which no issuer certificate is available,
  because it is missing in the server-provided chain and not available in the
  local certificate store. This is, with respect to trust, treated equivalent
  to a self-signed cert.

* Fix stream management state going out-of-sync when an errornous stanza
  (unknown payload, type or validator errors on the payload) was received.

* Move SASL XSOs to :mod:`aioxmpp.stream_xsos`; they are still (inofficially)
  available under their old name in :mod:`aioxmpp.sasl`.

* *Possibly breaking change*: :attr:`aioxmpp.xso.XSO.DECLARE_NS` is now
  automatically generated by the meta class
  :class:`aioxmpp.xso.XMLStreamClass`. See the documentation for the detailed
  rules.

  To get the old behaviour for your class, you have to put ``DECLARE_NS = {}``
  in its declaration.

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
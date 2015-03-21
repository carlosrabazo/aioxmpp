"""
:mod:`aioxmpp.xso` --- Working with XML stream contents
#######################################################

This subpackage deals with **X**\ ML **S**\ tream **O**\ bjects. XSOs can be
stanzas, but in general anything which is sent after the XML stream header.

The facilities in this subpackage are supposed to help developers of XEP
plugins, as well as the main development of :mod:`aioxmpp`. The subpackage
is split in two parts, :mod:`aioxmpp.xso.model`, which provides facilities to
allow declarative-style parsing and un-parsing of XML subtrees into XSOs and
the :mod:`aioxmpp.xso.types` module, which provides classes which implement
validators and type parsers for content represented as strings in XML.

Terminology
===========

Defenition of an XSO
--------------------

An XSO is an object whose class inherits from
:class:`aioxmpp.xso.XSO`.

A word on tags
--------------

Tags, as used by etree, are used throughout this module. Note that we are
representing tags as tuples of ``(namespace_uri, localname)``, where
``namespace_uri`` may be :data:`None`.

.. seealso::

   The functions :func:`normalize_tag` and :func:`tag_to_str` are useful to
   convert from and to ElementTree compatible strings.


Suspendable functions
---------------------

This module uses suspendable functions, implemented as generators, at several
points. These may also be called coroutines, but have nothing to do with
coroutines as used by :mod:`asyncio`, which is why we will call them
suspendable functions here.

Suspendable functions possibly take arguments and then operate on input which
is fed to them in a push-manner step by step (using the
:meth:`~types.GeneratorType.send` method). The main usage in this module is to
process SAX events: The SAX events are processed step-by-step by the functions,
and when the event is fully processed, it suspends itself (using ``yield``)
until the next event is sent into it.

General functions
=================

.. autofunction:: normalize_tag

.. autofunction:: tag_to_str

.. module:: aioxmpp.xso.model

.. currentmodule:: aioxmpp.xso

Object declaration with :mod:`~aioxmpp.xso.model`
=================================================

This module provides facilities to create classes which map to full XML stream
subtrees (for example stanzas including payload).

To create such a class, derive from :class:`XSO` and provide attributes
using the :class:`Attr`, :class:`Text`, :class:`Child` and :class:`ChildList`
descriptors.

Descriptors for XML-sourced attributes
--------------------------------------

The following descriptors can be used to load XSO attributes from XML. There
are two fundamentally different descriptor types: *scalar* and *non-scalar*
(e.g. list) descriptors. *scalar* descriptor types always accept a
value of :data:`None`, which represents the *absence* of the object (unless it
is required by some means, e.g. ``Attr(required=True)``). *Non-scalar*
descriptors generally have a different way to describe the absence and in
addition have a mutable value. Assignment to the descriptor attribute is
strictly type-checked.

Scalar descriptors
^^^^^^^^^^^^^^^^^^

.. autoclass:: Attr(name, type_=xso.String(), default=None, required=False, validator=None, validate=ValidateMode.FROM_RECV)

.. autoclass:: Child(classes, default=None)

.. autoclass:: ChildTag(tags, *, text_policy=UnknownTextPolicy.FAIL, child_policy=UnknownChildPolicy.FAILattr_policy=UnknownAttrPolicy.FAIL, default_ns=None, default=None, allow_none=False)

.. autoclass:: ChildText(tag, child_policy=UnknownChildPolicy.FAIL, attr_policy=UnknownAttrPolicy.FAIL, type_=xso.String(), default=None, validator=None, validate=ValidateMode.FROM_RECV)

.. autoclass:: Text(type_=xso.String(), default=None, validator=None, validate=ValidateMode.FROM_RECV)

Non-scalar descriptors
^^^^^^^^^^^^^^^^^^^^^^

.. autoclass:: ChildList(classes)

.. autoclass:: ChildMap(classes)

.. autoclass:: Collector()


Parsing XSOs
------------

To parse XSOs, an asynchronous approach which uses SAX-like events is
followed. For this, the suspendable functions explained earlier are used. The
main class to parse a XSO from events is :class:`XSOParser`. To drive
that suspendable callable from SAX events, use a :class:`SAXDriver`.

.. autoclass:: XSOParser

.. autoclass:: SAXDriver

Base and meta class
-------------------

The :class:`XSO` base class makes use of the :class:`XMLStreamClass`
metaclass and provides implementations for utility methods. For an object to
work with this module, it must derive from :class:`XSO` or provide an
identical interface.

.. autoclass:: XSO()

The metaclass takes care of collecting the special descriptors in attributes
where they can be used by the SAX event interpreter to fill the class with
data. It also provides a class method for late registration of child classes.

.. currentmodule:: aioxmpp.xso.model

.. autoclass:: XMLStreamClass

.. currentmodule:: aioxmpp.xso

Functions, enumerations and exceptions
--------------------------------------

The values of the following enumerations are used on "magic" attributes of
:class:`XMLStreamClass` instances (i.e. classes).

.. autoclass:: UnknownChildPolicy

.. autoclass:: UnknownAttrPolicy

.. autoclass:: UnknownTextPolicy

.. autoclass:: ValidateMode

The following exceptions are generated at some places in this module:

.. autoclass:: UnknownTopLevelTag

.. module:: aioxmpp.xso.types

.. currentmodule:: aioxmpp.xso

Types and validators from :mod:`~aioxmpp.xso.types`
===================================================

This module provides classes whose objects can be used as types and validators
in :mod:`~aioxmpp.xso.model`.

Types
-----

Types are used to convert strings obtained from XML character data or attribute
contents to python types. They are valid values for *type_* arguments e.g. for
:class:`~aioxmpp.xso.Attr`.

The basic type interface
^^^^^^^^^^^^^^^^^^^^^^^^

.. autoclass:: AbstractType

Implementations
^^^^^^^^^^^^^^^

.. autoclass:: String

.. autoclass:: Integer

.. autoclass:: Bool

.. autoclass:: DateTime

.. autoclass:: Base64Binary

.. autoclass:: HexBinary

.. autoclass:: JID

Validators
----------

Validators validate the python values after they have been parsed from
XML-sourced strings or even when being assigned to a descriptor attribute
(depending on the choice in the *validate* argument).

They can be useful both for defending and rejecting incorrect input and to
avoid producing incorrect output.

The basic validator interface
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. autoclass:: AbstractValidator

Implementations
^^^^^^^^^^^^^^^

.. autoclass:: RestrictToSet

.. autoclass:: Nmtoken


"""


def tag_to_str(tag):
    """
    *tag* must be a tuple ``(namespace_uri, localname)``. Return a tag string
    conforming to the ElementTree specification. Example::

         tag_to_str(("jabber:client", "iq")) == "{jabber:client}iq"
    """
    return "{{{:s}}}{:s}".format(*tag) if tag[0] else tag[1]


def normalize_tag(tag):
    """
    Normalize an XML element tree *tag* into the tuple format. The following
    input formats are accepted:

    * ElementTree namespaced string, e.g. ``{uri:bar}foo``
    * Unnamespaced tags, e.g. ``foo``
    * Two-tuples consisting of *namespace_uri* and *localpart*; *namespace_uri*
      may be :data:`None` if the tag is supposed to be namespaceless. Otherwise
      it must be, like *localpart*, a :class:`str`.

    Return a two-tuple consisting the ``(namespace_uri, localpart)`` format.
    """
    if isinstance(tag, str):
        namespace_uri, sep, localname = tag.partition("}")
        if sep:
            if not namespace_uri.startswith("{"):
                raise ValueError("not a valid etree-format tag")
            namespace_uri = namespace_uri[1:]
        else:
            localname = namespace_uri
            namespace_uri = None
        return (namespace_uri, localname)
    elif len(tag) != 2:
        raise ValueError("not a valid tuple-format tag")
    else:
        if any(part is not None and not isinstance(part, str) for part in tag):
            raise TypeError("tuple-format tags must only contain str and None")
        if tag[1] is None:
            raise ValueError("tuple-format localname must not be None")
    return tag


from .types import (  # NOQA
    AbstractType,
    String,
    Integer,
    Float,
    Bool,
    DateTime,
    Base64Binary,
    HexBinary,
    JID,
    AbstractValidator,
    RestrictToSet,
    Nmtoken
)

from .model import (  # NOQA
    tag_to_str,
    normalize_tag,
    UnknownChildPolicy,
    UnknownAttrPolicy,
    UnknownTextPolicy,
    ValidateMode,
    UnknownTopLevelTag,
    Attr,
    Child,
    ChildList,
    ChildMap,
    ChildTag,
    ChildText,
    Collector,
    Text,
    XSOParser,
    SAXDriver,
    XSO,
)
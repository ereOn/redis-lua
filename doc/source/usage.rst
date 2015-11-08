.. _usage:

Basic usage
===========

Files layout
------------

It is recommended to create dedicated folder in your project for your LUA
scripts.

A good convention is to name it `lua` as it is both obvious and short to type.

You can then organize your scripts in whichever structure you want: with or
without subfolders, one for each function or several functions per file. It's
really up to you. Just make sure you stay consistent.

A common pattern to get a variable that points to that root folder for scripts
is to write:

.. code-block:: python

   LUA_SCRIPTS_PATH = os.path.join(
       os.path.dirname(os.path.abspath(__file__)),
       'lua',
   )

Initialization
--------------

In a typical case, you want to load all your scripts in the initialization
of your executable or service. The easiest way to achieve that is to simply
call:

.. code-block:: python

   from redis_lua import load_all_scripts

   scripts = load_all_scripts(path=LUA_SEARCH_PATH)

Calling scripts
---------------

Calling a script is easy:

.. code-block:: python

   result = scripts['foo'].get_runner(client=client)(
       my_key='my_key',
       my_arg='my_arg',
   )

``result`` will contain the result as given by the LUA script.

Advanced usage
==============

`redis_lua` does not only provide helpers to deal with LUA scripts but also
extends the LUA syntax to add new features.

Keys, arguments and return values
---------------------------------

`redis_lua` helps you calling LUA scripts by allowing you to name your keys and
arguments.

To do that, you can use the `%key` and `%arg` instructions. Both are pretty
similar but don't have the exact same syntax.

Keys
++++

The `%key` instruction takes one mandatory parameter that is the name of the
key. Keys and arguments share the same namespace which means you can only have
one key or argument with a given name. To avoid ambiguity on the Python side,
it is recommended that you suffix your keys with `_key` as to make it obvious
you are dealing with a Redis key.

Here is an example of usage of the `%key` instruction:

.. code-block:: lua

   %key player_key

This exposes a `player_key` function argument on the Python side which expects
to be set with a Redis key (a string).

Arguments
+++++++++

The `%arg` instructions takes one mandatory parameter which is the name of the
argument, like `%key`, and one optional parameter, which is the type of the
argument.

Here is an example of usage of the `%arg` instruction:

.. code-block:: lua

   %arg count int

This exposes a `count` function argument on the Python side which expects to be
set with a Python integer value.

Here is a list of the supported types:

========== =========== ============
Aliases    Python type LUA type
========== =========== ============
int        int         number
integer    int         number
string     str         string
str        str         string
bool       bool        number
boolean    bool        number
dict       dict        array (dict)
dictionary dict        array (dict)
list       list        array
array      list        array
========== =========== ============

If no type is specified, the argument is transfered as-is to the script using
the default argument conversion of `pyredis`. It is unspecified what this
conversion does exactly.

Return values
+++++++++++++

The `%return` statement indicates the expected return type of the script when
converting the value for return on the Python side. The user is responsible for
providing a value that can correctly be cast to the registered return type.

Here is an example of usage of the `%return` instruction:

.. code-block:: lua

   %return dict

This cause the value returned by the script to be interpreted as a JSON-encoded
dictionary and converted implicitely into a Python `dict`.

Here is a list of the expected LUA types for each type:

========== =========== =========================
Aliases    Python type LUA type
========== =========== =========================
int        int         number
integer    int         number
string     str         string
str        str         string
bool       bool        number
boolean    bool        number
dict       dict        JSON-encoded array (dict)
dictionary dict        JSON-encoded array (dict)
list       list        JSON-encoded array
array      list        JSON-encoded array
========== =========== =========================

On the LUA side, you may want to use the following pattern for the ``list`` and
``dict`` return types:

.. code-block:: lua

   return cjson.encode({
      a=1,
      b="2",
      c={
        d=42,
      },
   })

.. warning::

   There can be at most **one** `%return` statement in a given script.

Script inclusion
----------------

One of the main problems of Redis LUA scripts is that it doesn't support the
LUA ``require`` keyword. To circumvent that limitation, the LUA script parsing
logic in `redis_lua` handles ``%include`` statements, like so:

.. code-block:: lua

   -- The "foo.lua" script in the same folder defines the "create_foo()"
   -- function.

   %include "foo"

   local t = create_foo(1, "a");

`%include` takes a single argument, which is the complete name (with any
relative path component) of the LUA script to include, without its ``.lua``
extension.

So if you have two scripts ``foo/a.lua`` and ``bar/b.lua`` each in a different
subfolder of the ``lua`` directory, you can include ``bar/b.lua`` in
``foo/a.lua`` by simply adding the following `%include` statement:

.. code-block:: lua

   %include '../bar/b'

.. warning::

   For the inclusion system to work properly, all scripts must either been have
   loaded by the same call, or by different calls but using the same script
   cache.

Multiple inclusion
++++++++++++++++++

By default, `redis-lua` allows multiple inclusions of the same file several
times. This can cause issues when including different scripts that include the
same subscripts which conflict with each other.

To prevent side-effects caused by multiple inclusion of the same scripts, you
can use the following statement, anywhere in the script:

.. code-block:: lua

   %pragma once

.. note::

   This behavior is new since version 2.0.0.

   In previous versions, the default behavior was as-if `%pragma once` was
   defined implicitely in each script.

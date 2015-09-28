.. _index:

Welcome to redis-lua's documentation!
=====================================

`redis-lua` is a pure-Python library that eases usage of LUA scripts with
Redis. It provides script loading and parsing abilities as well as testing
primitives.

Quick start
-----------

A code sample is worth a thousand words:

.. code-block:: python

   from redis_lua import load_script

   # Loads the 'create_foo.lua' in the 'lua' directory.
   script = load_script(name='create_foo', path='lua/')

   # Run the script with the specified arguments.
   foo = script.get_runner(client=redis_client)(
       members={'john', 'susan', 'bob'},
       size=5,
   )

Step-by-step analysis
+++++++++++++++++++++

Let's go through the code sample step by step.

First we have:

.. code-block:: python

   from redis_lua import load_script

We import the only function we need. Nothing too specific here.

The next lines are:

.. code-block:: python

   # Loads the 'create_foo.lua' in the 'lua' directory.
   script = load_script(name='create_foo', path='lua/')


These lines looks for a file named `create_foo.lua` in the `lua` directory,
relative to the current working directory. This example actually considers
that using the current directory is correct. In a production code, you likely
want to make sure to use a more reliable or absolute path.

The :py:func:`load_script <redis_lua.load_script>` function takes the name of
the script to load, without its `.lua` extension and a path to search from. It
supports sub-directories which means that specifying `subdir/foo` in the path
`lua/` will actually look for the file `lua/subdir/foo.lua`. It returns a
:py:class:`Script <redis_lua.script.Script>` instance.

In production code, you will likely want to load several scripts at once. To
this intent, you can either use :py:func:`load_scripts
<redis_lua.load_scripts>` which takes a list of names or
:py:func:`load_all_scripts <redis_lua.load_all_scripts>` which loads all the
scripts it can find in a given directory. The former gives you better, explicit
control over which files you load and the latter in nice in case where you want
to load every script.

Finally we have:

.. code-block:: python

   # Run the script with the specified arguments.
   foo = script.get_runner(client=redis_client)(
       members={'john', 'susan', 'bob'},
       size=5,
   )

This basically tells the specified Redis instance to execute the script with
the specified parameters and to give us back the result. Note how `redis_lua`
translated all the arguments and the return value for you transparently. We
will see in a moment what it takes to reach that level of user-friendlyness.

The :py:func:`Script.get_runner <redis_lua.script.Script.get_runner>` method
takes either a Redis connection or a pipeline and returns a callable. This
callable expects in turn the named arguments to call the script with and
returns the script's return value.

What's the magic at play here ?
-------------------------------

You may wonder how it is possible for `redis_lua` to possibly know how to
translate the `members` and `size` arguments to something meaningful in LUA.

Let's take a look at the `create_foo.lua` file:

.. code-block:: lua

   %arg size integer
   %arg members list
   %return dict
   
   local foo_id = redis.call('INCR', 'foo:last_id')
   local foo_root_key = string.format('foo:%s', foo_id)
   local foo_members_key = foo_root_key .. ':members'
   local foo_size_key = foo_root_key .. ':size'
   
   redis.call('SET', foo_size_key, size)
   redis.call('SADD', foo_members_key, unpack(members))
   
   return cjson.encode({
       id=foo_id,
       members=members,
       size=size,
   })

Notice the `%arg` and `%return` lines ? This is where the magic happens.

`redis_lua` extends the language of LUA scripts with new instructions to
instrument your scripts. A `%arg` instruction declares a named variable and its
type so that it gets converted for you automatically when calling the script. A
`%return` statement declares the expected return type of the LUA script so that
you don't have to parse it yourself.

You will never have to write things like this anymore:

.. code-block:: lua

   local size = tonumber(ARGV[1]) -- So size goes first. I'll have to remember
                                  -- that when calling the script.
   local members = cjson.decode(ARGV[2]) -- Don't forget to increment ARGV !

One step further
----------------

Aren't you tired of duplicating logic in your LUA scripts just because the
`require` instruction isn't available in Redis LUA ?

Well, you won't have to do that anymore: `redis_lua` not only supports named
arguments but also recursive `%include` directives ! Split your scripts in as
many files as you want and simply assemble them using the appropriate
`%include` statements ! `redis_lua` will take care of concatening the different
scripts for you automatically.

What happens when I make a mistake ?
------------------------------------

At this point, you might be afraid that extending the language with new
instructions and include capabilities causes you troubles when something wrong
happens in your LUA script. Fear no longer: `redis_lua` not only extends the
langage but also improves the debugging and testing tools.

Let's introduce a problem in our script and look at the resulting exception:

.. code-block:: none

   redis_lua.exceptions.ScriptError: Script attempted to access unexisting global variable 'foo_size_key'
   LUA Traceback (most recent script last):
     Script "<user-code>", line 8
       local foo_size_key = foo_size_key .. ':size'

The LUA scripting error was detected as usual by `redispy` but `redis_lua` was
able to enhance it with more contextual information: the script in which the
error occured, the line at which it occured and the offending code. Had the
error happened in a sub-script (via an `%include` directive), the traceback of
the different scripts would have been shown as well. Simple, reliable and
efficient.

What's next ?
-------------

Check out the :ref:`api` for more details about the available functions.

Table of contents
=================

.. toctree::
   :maxdepth: 2

   usage
   api

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

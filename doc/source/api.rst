.. _api:

API
===

Script loading functions
------------------------

These functions are the most common entry points for loading LUA scripts on
disk.

.. autofunction:: redis_lua.load_all_scripts
.. autofunction:: redis_lua.load_scripts
.. autofunction:: redis_lua.load_script

Script running functions
------------------------

These functions are using to execute LUA code on Redis servers.

.. autofunction:: redis_lua.run_code

Script instances
----------------

All loaded scripts are wrapped into a :py:class:`redis_lua.script.Script`
instance.

.. autoclass:: redis_lua.script.Script
   :members:

Low-level script functions
--------------------------

These functions are useful for people that want to perform more advanced
operations, such as parsing a Script file manually from another source than a
file.

.. autofunction:: redis_lua.read_script
.. autofunction:: redis_lua.parse_script

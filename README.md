[![Build Status](https://travis-ci.org/ereOn/redis-lua.svg?branch=master)](https://travis-ci.org/ereOn/redis-lua)
[![Coverage Status](https://coveralls.io/repos/ereOn/redis-lua/badge.svg?branch=master&service=github)](https://coveralls.io/github/ereOn/redis-lua?branch=master)
[![Documentation Status](https://readthedocs.org/projects/redis-lua/badge/?version=latest)](http://redis-lua.readthedocs.org/en/latest/?badge=latest)
[![PyPI](https://img.shields.io/pypi/pyversions/redis-lua.svg)](https://pypi.python.org/pypi/redis-lua/1.0.0)
[![GitHub tag](https://img.shields.io/github/tag/ereOn/redis-lua.svg)](https://github.com/ereOn/redis-lua)
[![PyPi version](https://img.shields.io/pypi/v/redis-lua.svg)](https://pypi.python.org/pypi/redis-lua/1.0.0)
[![PyPi downloads](https://img.shields.io/pypi/dm/redis-lua.svg)](https://pypi.python.org/pypi/redis-lua/1.0.0)

# redis-lua
**redis-lua** is a pure-Python library that eases usage of LUA scripts with Redis. It provides script loading and parsing abilities as well as testing primitives.

## Quick start
A code sample is worth a thousand words:

    from redis_lua import load_script

    # Loads the 'create_foo.lua' in the 'lua' directory.
    script = load_script(name='create_foo', path='lua/')

    # Run the script with the specified arguments.
    foo = script.get_runner(client=redis_client)(
        members={'john', 'susan', 'bob'},
        size=5,
    )

This sample code simply loads a LUA script from disk and executes it on the specified Redis instance by specifying named arguments of various types. How simpler can it get ?

Check out the [documentation](http://redis-lua.readthedocs.org/en/latest/?badge=latest) to find out more !

## Installation

Just type:

> pip install redis-lua

That's it.

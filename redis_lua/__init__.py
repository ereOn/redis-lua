"""
Helpers to ease LUA scripting with Redis.
"""

import os
import six

from functools import partial

from .exceptions import (
    CyclicDependencyError,
    ScriptNotFoundError,
)
from .regions import ScriptParser
from .script import Script


def load_all_scripts(path, cache=None):
    """
    Load all the LUA scripts found at the specified location.

    :param path: A path to search into for LUA scripts.
    :param cache: A cache of scripts to use to fasten loading. If some `names`
        are in the `cache`, then they are taken from it.
    :return: A list of scripts that were found, in arbitrary order.
    """
    if cache is None:
        cache = {}

    scripts = {}

    for root, dirs, files in os.walk(path):
        prefix = os.path.relpath(root, path)
        scripts.update(load_scripts(
            names=[
                os.path.splitext(
                    os.path.normpath(os.path.join(prefix, file_)),
                )[0]
                for file_ in files
            ],
            path=path,
            cache=cache,
        ))

    return scripts


def load_scripts(names, path, cache=None):
    """
    Load several LUA scripts.

    :param names: An iterable of LUA scripts names to load. If some names
        contain backslashes, those will be replaced with forward slashes
        silently.
    :param path: A path to search into for LUA scripts.
    :param cache: A cache of scripts to use to fasten loading. If some `names`
        are in the `cache`, then they are taken from it.

    :return: A dict of scripts that were found.

    :warning: All scripts whose load succeeds are added in the cache
        immediately. This means that if some script fails to load and the
        function call throws, the cache will still have been updated.
    """
    if cache is None:
        cache = {}

    return {
        script.name: script
        for script in (
            load_script(
                name=name,
                path=path,
                cache=cache,
            )
            for name in names
        )
    }


def load_script(name, path, cache=None, ancestors=None):
    """
    Load a LUA script.

    :param name: The name of the LUA script to load, relative to the search
        `path`, without the '.lua' extension. If the name contains backslashes,
        those will be replaced with forward slashes silently.
    :param path: A path to search into for LUA scripts.
    :param cache: A cache of scripts to use to fasten loading. If `name` is in
        the `cache`, then the result is the same as calling `cache[name]`.
    :param ancestors: A list of names to consider as ancestors scripts.
    :return: A :py:class:`Script <redis_lua.script.Script>` instance.
    """
    if cache:
        result = cache.get(name)

        if result:
            return result

    name = name.replace(os.path.sep, '/')
    content = read_script(name=name, path=path)

    return parse_script(
        name=name,
        content=content,
        path=path,
        cache=cache,
        ancestors=ancestors,
    )


def _get_cycle(name, ancestors):
    return ancestors[ancestors.index(name):] + [name]


def parse_script(
    name,
    content,
    path=None,
    cache=None,
    ancestors=None,
):
    """
    Parse a LUA script.

    :param name: The name of the LUA script to parse.
    :param content: The content of the script.
    :param path: The path of the script. Can be `None` if the script was loaded
        from memory. In this case, any included script must exist in the cache.
    :param cache: A dict of scripts that were already parsed. The resulting
        script is added to the cache. If the currently parsed script exists in
        the cache, it will be overriden.
    :param ancestors: A list of scripts that were called before this one. Used
        to detect infinite recursion.
    :return: A :py:class:`Script <redis_lua.script.Script>` instance.
    """
    if not ancestors:
        ancestors = []
    elif name in ancestors:
        raise CyclicDependencyError(
            cycle=_get_cycle(name=name, ancestors=ancestors),
        )

    if cache is None:
        cache = {}

    script = ScriptParser().parse(
        name=name,
        content=content,
        script_class=Script,
        get_script_by_name=partial(
            load_script,
            path=path,
            cache=cache,
            ancestors=ancestors + [name],
        ),
    )
    cache[name] = script

    return script


def read_script(name, path, encoding=None):
    """
    Read a LUA script.

    :param name: The name of the LUA script to load, relative to the search
        `paths`, without the '.lua' extension. `name` may contain forward slash
        path separators to indicate that the script is to be found in a
        sub-directory.
    :param path: A path to search into for LUA scripts.
    :param encoding: The encoding to use to read the file. If none is
        specified, UTF-8 is assumed.
    :return: The content of the script.
    :raises: If no such script is found, a
        :py:class:`ScriptNotFoundError
        <redis_lua.exceptions.ScriptNotFoundError>` is thrown.
    """
    assert path is not None

    filename = os.path.normpath(os.path.join(
        path,
        "{}.lua".format(name.replace('/', os.path.sep)),
    ))

    if encoding is None:
        encoding = 'utf-8'

    try:
        if six.PY2:
            with open(filename) as _file:
                return _file.read().decode(encoding)
        else:
            with open(filename, encoding=encoding) as _file:
                return _file.read()

    except IOError:
        raise ScriptNotFoundError(name=name, filename=filename)


def run_code(
    client,
    content,
    path=None,
    kwargs=None,
    cache=None,
):
    """
    Run a LUA `script` on the specified `redis` instance.

    :param client: The Redis or pipeline instance to execute the script on.
    :param content: The LUA code to execute.
    :param path: The path to search for for scripts inclusion. Can be `None`,
        in which case, any included script must exist in the cache.
    :param kwargs: A dict of arguments to call the script with.
    :param cache: The script cache to use to fasten script inclusion.
    :return: The return value, as given by the script.
    """
    name = '<user-code>'
    script = parse_script(
        name=name,
        content=content,
        path=path,
        cache=cache,
    )

    if not kwargs:
        kwargs = {}

    return script.get_runner(client)(**kwargs)

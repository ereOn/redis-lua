"""
LUA scripts-related functions.
"""

import six

from redis.client import Script as RedisScript

from .exceptions import error_handler
from .regions import (
    ArgumentRegion,
    KeyRegion,
    ScriptRegion,
)


@six.python_2_unicode_compatible
class Script(object):
    def __init__(self, name, regions, registered_client):
        """
        Create a new script object.

        :param name: The name of the script, without its `.lua` extension.
        :param regions: A non-empty list of regions that compose the script.
        :param registered_client: A Redis instance or pipeline to execute the
            script on by default.
        """
        if not regions:
            raise ValueError('regions cannot be empty')

        self.name = name
        self.regions = regions
        self.redis_script = RedisScript(
            registered_client=registered_client,
            script=self.content,
        )

    def __repr__(self):
        return '{_class}(name={self.name!r})'.format(
            _class=self.__class__.__name__,
            self=self,
        )

    def __hash__(self):
        return hash(self.name)

    @property
    def content(self):
        return '\n'.join(map(six.text_type, self.regions))

    @property
    def line_count(self):
        return sum(region.line_count for region in self.regions)

    @property
    def real_line_count(self):
        return sum(region.real_line_count for region in self.regions)

    def get_real_line_content(self, line):
        """
        Get the real line content for the script at the specified line.

        :param line: The line.
        :returns: A line content.
        """
        region, real_line = self.get_region_for_line(line)

        if isinstance(region, ScriptRegion):
            return region.content
        else:
            return region.content.split('\n')[real_line - region.real_line]

    def get_scripts_for_line(self, line):
        """
        Get the list of (script, line) by order of traversal for a given line.

        :param line: The line.
        :returns: A list of (script, line) that got traversed by that line.
        """
        region, real_line = self.get_region_for_line(line)
        result = [(self, real_line)]

        if isinstance(region, ScriptRegion):
            result.extend(
                region.script.get_scripts_for_line(line - region.line + 1),
            )

        return result

    def get_region_for_line(self, line):
        """
        Get the region and real line in this script that matches the specified
        line.

        :param line: The line.
        :returns: The (region, real_line) or `ValueError` if no such line
            exists.
        """
        if line < 1 or line > self.line_count:
            raise ValueError("No such line %d in script %s" % (line, self))

        for index, region in reversed(list(enumerate(self.regions))):
            if region.line <= line:
                if isinstance(region, ScriptRegion):
                    return region, region.real_line
                else:
                    real_lines_before = sum(
                        region.real_line_count
                        for region in self.regions[:index]
                    )

                    return region, real_lines_before + (line - region.line) + 1

    @property
    def keys(self):
        result = []

        for region in self.regions:
            if isinstance(region, KeyRegion):
                result.append((region.name, region.index))
            elif isinstance(region, ScriptRegion):
                result.extend(
                    (name, index + len(result))
                    for name, index in region.script.keys
                )

        return result

    @property
    def arguments(self):
        result = []

        for region in self.regions:
            if isinstance(region, ArgumentRegion):
                result.append((region.name, region.index, region.type_))
            elif isinstance(region, ScriptRegion):
                result.extend(
                    (name, index + len(result), type_)
                    for name, index, type_ in region.script.arguments
                )

        return result

    def __str__(self):
        return self.name + ".lua"

    def __eq__(self, other):
        if not isinstance(other, Script):
            return NotImplemented

        return all([
            other.name == self.name,
            other.regions == self.regions,
        ])

    def on_client(self, registered_client):
        """
        Return a copy of the Script instance that runs on the specified client.

        :param registered_client: The Redis instance or pipeline to run the
            script on.
        :returns: A copy of the current Script instance on which you can
        perform a direct call.
        """
        # Optimization: if the client is the same as the current one, we don't
        # recreate an instance to avoid a guaranteed cache miss in redis-py
        # code.
        if registered_client == self.redis_script.registered_client:
            return self

        return self.__class__(
            name=self.name,
            regions=self.regions,
            registered_client=registered_client,
        )

    def __call__(self, **kwargs):
        """
        Call the script with its named arguments.

        :returns: The script result.
        """
        keys = [key for key, _ in self.keys]
        arguments = [argument for argument, _, _ in self.arguments]
        sentinel = object()
        keys_params = [sentinel] * len(keys)
        args_params = [sentinel] * len(arguments)

        for key, value in kwargs.items():
            if key in keys:
                index = keys.index(key)
                keys_params[index] = value

            elif key in arguments:
                index = arguments.index(key)
                args_params[index] = value

            else:
                raise TypeError("Unknown key-argument %r" % key)

        missing_keys = {
            key
            for index, key in enumerate(keys)
            if keys_params[index] is sentinel
        }

        if missing_keys:
            raise TypeError("Missing key-argument(s) %r" % list(missing_keys))

        missing_arguments = {
            argument
            for index, argument in enumerate(arguments)
            if args_params[index] is sentinel
        }

        if missing_arguments:
            raise TypeError(
                "Missing key-argument(s) %r" % list(missing_arguments),
            )

        with error_handler(self):
            return self.redis_script(
                client=None,
                keys=keys_params,
                args=args_params,
            )

"""
LUA scripts-related functions.
"""

import json
import six

from redis.client import Script as RedisScript

from .exceptions import error_handler
from .regions import (
    ArgumentRegion,
    KeyRegion,
    ReturnRegion,
    ScriptRegion,
)
from .render import RenderContext


@six.python_2_unicode_compatible
class Script(object):
    @classmethod
    def get_keys_from_regions(cls, regions):
        result = []

        for region in regions:
            if isinstance(region, KeyRegion):
                if region.index != len(result) + 1:
                    raise ValueError(
                        "Encountered key %s with index %d when index %d was "
                        "expected" % (
                            region.name,
                            region.index,
                            len(result) + 1,
                        )
                    )

                result.append(region.name)
            elif isinstance(region, ScriptRegion):
                result.extend(cls.get_keys_from_regions(region.script.regions))

        duplicates = {x for x in result if result.count(x) > 1}

        if duplicates:
            raise ValueError("Duplicate key(s) %r" % list(duplicates))

        return result

    @classmethod
    def get_args_from_regions(cls, regions):
        result = []

        for region in regions:
            if isinstance(region, ArgumentRegion):
                if region.index != len(result) + 1:
                    raise ValueError(
                        "Encountered argument %s with index %d when index %d "
                        "was expected" % (
                            region.name,
                            region.index,
                            len(result) + 1,
                        )
                    )

                result.append((region.name, region.type_))
            elif isinstance(region, ScriptRegion):
                result.extend(cls.get_args_from_regions(region.script.regions))

        duplicates = {x for x in result if result.count(x) > 1}

        if duplicates:
            raise ValueError("Duplicate arguments(s) %r" % list(duplicates))

        return result

    @classmethod
    def get_return_from_regions(cls, regions):
        result = None

        for region in regions:
            if isinstance(region, ReturnRegion):
                if result is not None:
                    raise ValueError("There can be only one return statement.")

                result = region.type_

        return result

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
        self.keys = self.get_keys_from_regions(regions)
        self.args = self.get_args_from_regions(regions)
        self.return_type = self.get_return_from_regions(regions)

        duplicates = set(self.keys) & {arg for arg, _ in self.args}

        if duplicates:
            raise ValueError(
                'Some key(s) and argument(s) have the same names: %r' % list(
                    duplicates,
                ),
            )

        self.regions = regions
        self.redis_script = RedisScript(
            registered_client=registered_client,
            script=self.render(),
        )

    def __repr__(self):
        return '{_class}(name={self.name!r})'.format(
            _class=self.__class__.__name__,
            self=self,
        )

    def __hash__(self):
        return hash(self.name)

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

    def __str__(self):
        return self.name + ".lua"

    def render(self, context=None):
        if context is None:
            context = RenderContext()

        return context.render_script(self)

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

    @classmethod
    def convert_argument_for_call(cls, type_, value):
        if type_ is str:
            return str(value)
        elif type_ is int:
            return int(value)
        elif type_ is bool:
            return 1 if value else 0
        elif type_ is list:
            return json.dumps(list(value))
        elif type_ is dict:
            return json.dumps(dict(value))

    @classmethod
    def convert_return_value_from_call(cls, type_, value):
        if type_ is str:
            return str(value)
        elif type_ is int:
            return int(value)
        elif type_ is bool:
            return bool(value)
        elif type_ in [list, dict]:
            if isinstance(value, six.binary_type):
                value = value.decode('utf-8')

            return json.loads(value)
        else:
            return value

    def __call__(self, **kwargs):
        """
        Call the script with its named arguments.

        :returns: The script result.
        """
        sentinel = object()
        keys = {
            key: index
            for index, key
            in enumerate(self.keys)
        }
        args = {
            arg: (index, type_)
            for index, (arg, type_)
            in enumerate(self.args)
        }
        keys_params = [sentinel] * len(self.keys)
        args_params = [sentinel] * len(self.args)

        for name, value in kwargs.items():
            try:
                index = keys[name]
                keys_params[index] = value
            except KeyError:
                try:
                    index, type_ = args[name]
                    args_params[index] = self.convert_argument_for_call(
                        type_,
                        value,
                    )
                except KeyError:
                    raise TypeError("Unknown key/argument %r" % name)

        missing_keys = {
            key
            for key, index in keys.items()
            if keys_params[index] is sentinel
        }

        if missing_keys:
            raise TypeError("Missing key(s) %r" % list(missing_keys))

        missing_args = {
            arg
            for arg, (index, type_) in args.items()
            if args_params[index] is sentinel
        }

        if missing_args:
            raise TypeError(
                "Missing argument(s) %r" % list(missing_args),
            )

        with error_handler(self):
            result = self.redis_script(
                client=None,
                keys=keys_params,
                args=args_params,
            )
            return self.convert_return_value_from_call(
                self.return_type,
                result,
            )

"""
LUA scripts-related functions.
"""

import json
import six

from collections import namedtuple
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

    _LineInfo = namedtuple(
        '_LineInfo',
        [
            'first_real_line',
            'real_line',
            'real_line_count',
            'first_line',
            'line',
            'line_count',
            'region',
        ],
    )

    @classmethod
    def get_line_info_for_regions(cls, regions, included_scripts):
        """
        Get a list of tuples (first_real_line, real_line, real_line_count,
        first_line, line, line_count, region) for the specified list of
        regions.

        :params regions: A list of regions to get the line information from.
        :params included_scripts: A set of scripts that were visited already.
        :returns: A list of tuples.
        """
        result = []
        real_line = 1
        line = 1

        def add_region(real_line, line, region):
            result.append(
                cls._LineInfo(
                    real_line,
                    real_line,
                    region.real_line_count,
                    line,
                    line,
                    region.line_count,
                    region,
                ),
            )

        for region in regions:
            if isinstance(region, ScriptRegion):
                if region.script in included_scripts:
                    real_line += region.real_line_count
                    continue

                included_scripts.add(region.script)
                sub_result = cls.get_line_info_for_regions(
                    regions=region.script.regions,
                    included_scripts=included_scripts,
                )
                add_region(real_line, line, region)
                real_line += region.real_line_count
                line += sub_result[-1].line + sub_result[-1].line_count - 1
            else:
                add_region(real_line, line, region)
                real_line += region.real_line_count
                line += region.line_count

        return result

    def __init__(self, name, regions):
        """
        Create a new script object.

        :param name: The name of the script, without its `.lua` extension.
        :param regions: A non-empty list of regions that compose the script.
        """
        if not regions:
            raise ValueError('regions cannot be empty')

        self.name = name
        self.keys = self.get_keys_from_regions(regions)
        self.args = self.get_args_from_regions(regions)
        self.return_type = self.get_return_from_regions(regions)
        self.line_infos = self.get_line_info_for_regions(regions, {self})

        duplicates = set(self.keys) & {arg for arg, _ in self.args}

        if duplicates:
            raise ValueError(
                'Some key(s) and argument(s) have the same names: %r' % list(
                    duplicates,
                ),
            )

        self.regions = regions
        self._redis_scripts = {}

    def __repr__(self):
        return '{_class}(name={self.name!r})'.format(
            _class=self.__class__.__name__,
            self=self,
        )

    def __hash__(self):
        return hash(self.name)

    @property
    def line_count(self):
        info = self.line_infos[-1]

        return info.line + info.line_count - 1

    @property
    def real_line_count(self):
        info = self.line_infos[-1]

        return info.real_line + info.real_line_count - 1

    def get_real_line_content(self, line):
        """
        Get the real line content for the script at the specified line.

        :param line: The line.
        :returns: A line content.
        """
        info = self.get_line_info(line)

        if isinstance(info.region, ScriptRegion):
            return info.region.content
        else:
            return info.region.content.split('\n')[line - info.first_line]

    def get_scripts_for_line(self, line):
        """
        Get the list of (script, line) by order of traversal for a given line.

        :param line: The line.
        :returns: A list of (script, line) that got traversed by that line.
        """
        info = self.get_line_info(line)
        result = [(self, info.real_line)]

        if isinstance(info.region, ScriptRegion):
            result.extend(
                info.region.script.get_scripts_for_line(
                    line - info.first_line + 1,
                ),
            )

        return result

    def get_line_info(self, line):
        """
        Get the line information for the specified line.

        :param line: The line.
        :returns: The (real_line, real_line_count, line, line_count, region)
            tuple or `ValueError` if no such line exists.
        """
        for info in self.line_infos:
            if line >= info.line and line < info.line + info.line_count:
                return self._LineInfo(
                    first_real_line=info.first_real_line,
                    real_line=info.real_line + min(
                        line - info.line,
                        info.real_line_count - 1,
                    ),
                    real_line_count=info.real_line_count,
                    first_line=info.first_line,
                    line=line,
                    line_count=info.line_count,
                    region=info.region,
                )

        raise ValueError("No such line %d in script %s" % (line, self))

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

    @classmethod
    def convert_argument_for_call(cls, type_, value):
        if type_ is int:
            return int(value)
        elif type_ is bool:
            return 1 if value else 0
        elif type_ is list:
            return json.dumps(list(value))
        elif type_ is dict:
            return json.dumps(dict(value))
        else:
            return str(value)

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

    def get_redis_script(self, client):
        """
        Return a `RedisScript` instance associated to the specified client.

        :param client: The Redis client instance to get a `RedisScript`
            instance for.
        :returns: A `RedisScript` instance.
        """
        redis_script = self._redis_scripts.get(client)

        if redis_script is None:
            redis_script = RedisScript(
                registered_client=client,
                script=self.render(),
            )
            self._redis_scripts[client] = redis_script

        return redis_script

    def get_runner(self, client):
        """
        Get a runner for the script on the specified `client`.

        :param client: The Redis instance to call the script on.
        :returns: The runner, a callable that takes the script named arguments
            and returns its result.
        """
        def runner(**kwargs):
            """
            Call the script with its named arguments.

            :param client: The Redis instance to call the script on.
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
                result = self.get_redis_script(client)(
                    keys=keys_params,
                    args=args_params,
                )
                return self.convert_return_value_from_call(
                    self.return_type,
                    result,
                )

        return runner

"""
Scripts regions.
"""

import os
import re
import six


@six.python_2_unicode_compatible
class ScriptRegion(object):
    def __init__(self, script, real_line, line, content):
        self.script = script
        self.real_line = real_line
        self.line = line
        self.real_line_count = 1
        self.content = content

    def __repr__(self):
        return (
            '{_class}(real_line={self.real_line}, line={self.line}, '
            'line_count={self.line_count}, script=\'{self.script}\', '
            'content={self.content!r})'
        ).format(
            _class=self.__class__.__name__,
            self=self,
        )

    @property
    def line_count(self):
        return self.script.line_count

    def __str__(self):
        return self.script.content

    def __eq__(self, other):
        if not isinstance(other, ScriptRegion):
            return NotImplemented

        return all([
            other.script == self.script,
            other.real_line == self.real_line,
            other.line == self.line,
            other.content == self.content,
        ])

    @property
    def keys(self):
        return self.script.keys

    @property
    def args(self):
        return self.script.args


@six.python_2_unicode_compatible
class KeyRegion(object):
    def __init__(self, name, index, real_line, line, content):
        self.name = name
        self.index = index
        self.real_line = real_line
        self.line = line
        self.line_count = 1
        self.real_line_count = 1
        self.content = content

    def __repr__(self):
        return (
            '{_class}(real_line={self.real_line}, line={self.line}, '
            'line_count={self.line_count}, name=\'{self.name}\', '
            'content={self.content!r})'
        ).format(
            _class=self.__class__.__name__,
            self=self,
        )

    def __str__(self):
        return "local {self.name} = KEYS[{self.index}]".format(self=self)

    def __eq__(self, other):
        if not isinstance(other, KeyRegion):
            return NotImplemented

        return all([
            other.name == self.name,
            other.index == self.index,
            other.real_line == self.real_line,
            other.line == self.line,
            other.content == self.content,
        ])


@six.python_2_unicode_compatible
class ArgumentRegion(object):
    VALID_TYPES = {
        None: str,
        'int': int,
        'integer': int,
        'string': str,
        'str': str,
        'bool': bool,
        'boolean': bool,
    }

    @classmethod
    def get_valid_type(cls, type_):
        result = cls.VALID_TYPES.get(type_)

        if result is None:
            raise ValueError("Invalid type '%s' for argument" % type_)

        return result

    def __init__(self, name, index, type_, real_line, line, content):
        self.name = name
        self.index = index
        self.type_ = self.get_valid_type(type_=type_)
        self.real_line = real_line
        self.line = line
        self.line_count = 1
        self.real_line_count = 1
        self.content = content

    def __repr__(self):
        return (
            '{_class}(real_line={self.real_line}, line={self.line}, '
            'line_count={self.line_count}, name=\'{self.name}\', '
            'content={self.content!r})'
        ).format(
            _class=self.__class__.__name__,
            self=self,
        )

    def __str__(self):
        if self.type_ is int:
            return "local {self.name} = tonumber(ARGV[{self.index}])".format(
                self=self,
            )
        elif self.type_ is bool:
            return (
                "local {self.name} = tonumber(ARGV[{self.index}]) ~= 0"
            ).format(
                self=self,
            )
        else:
            return "local {self.name} = ARGV[{self.index}]".format(self=self)

    def __eq__(self, other):
        if not isinstance(other, ArgumentRegion):
            return NotImplemented

        return all([
            other.name == self.name,
            other.index == self.index,
            other.type_ == self.type_,
            other.real_line == self.real_line,
            other.line == self.line,
            other.content == self.content,
        ])


@six.python_2_unicode_compatible
class TextRegion(object):
    __slots__ = [
        'content',
        'real_line',
        'line',
        'line_count',
        'real_line_count',
    ]

    def __init__(self, content, real_line, line):
        self.content = content
        self.real_line = real_line
        self.line = line
        self.line_count = len(content.split('\n'))
        self.real_line_count = self.line_count

    def __repr__(self):
        return (
            '{_class}(real_line={self.real_line}, line={self.line}, '
            'line_count={self.line_count})'
        ).format(
            _class=self.__class__.__name__,
            self=self,
        )

    def __str__(self):
        return self.content

    def __eq__(self, other):
        if not isinstance(other, TextRegion):
            return NotImplemented

        return all([
            other.content == self.content,
            other.real_line == self.real_line,
            other.line == self.line,
        ])


class ScriptParser(object):
    """
    Parse LUA scripts.
    """

    class ParseRegionsContext(object):
        def __init__(self):
            self.regions = []
            self.first_real_line = 1
            self.offset = 0
            self.text_lines = []
            self.key_index = 1
            self.arg_index = 1

        def add_line(self, real_line, content):
            if not self.text_lines:
                self.first_real_line = real_line

            self.text_lines.append(content)

        def flush(self):
            if self.text_lines:
                self.regions.append(
                    TextRegion(
                        content='\n'.join(self.text_lines),
                        real_line=self.first_real_line,
                        line=self.first_real_line + self.offset,
                    ),
                )
                self.text_lines = []

        def add_script_region(self, real_line, script, content):
            self.flush()

            region = ScriptRegion(
                script=script,
                real_line=real_line,
                line=real_line + self.offset,
                content=content,
            )
            self.regions.append(region)

            self.offset += script.line_count - region.real_line_count
            self.key_index += len(script.keys)
            self.arg_index += len(script.args)

        def add_key_region(self, real_line, name, content):
            self.flush()

            region = KeyRegion(
                name=name,
                index=self.key_index,
                real_line=real_line,
                line=real_line + self.offset,
                content=content,
            )
            self.regions.append(region)
            self.key_index += 1

        def add_argument_region(self, real_line, name, type_, content):
            self.flush()

            region = ArgumentRegion(
                name=name,
                index=self.arg_index,
                type_=type_,
                real_line=real_line,
                line=real_line + self.offset,
                content=content,
            )
            self.regions.append(region)
            self.arg_index += 1

        def normalize(self):
            self.flush()

            if not self.regions:
                self.add_line(1, '')
                self.flush()

    def parse(self, name, content, script_class, get_script_by_name):
        """
        Parse a LUA script.

        :param name: The name of the LUA script to parse.
        :param content: The content of the script.
        :param script_class: A callable that creates
            :py:class:`Script<redis_lua.script.Script>` instances. Must take
            `name` and `regions` named arguments.
        :param get_script_by_name: A callable that takes a named `name`
            argument (the name of the script) and returns a :py:class:`Script
            <redis_lua.script.Script>` instance.
        :return: A `Script` instance.
        """
        regions = self.parse_regions(
            content=content,
            current_path=os.path.dirname(name),
            get_script_by_name=get_script_by_name,
        )
        return script_class(name=name, regions=regions)

    def parse_regions(self, content, current_path, get_script_by_name):
        """
        Parse a LUA script and split it into regions.

        :param content: The content of the script to parse.
        :param current_path: The current path the parsing is taking place. Used
            to process file-relative statements.
        :param get_script_by_name: A callable that takes a named `name`
            argument (the name of the script) and returns a :py:class:`Script
            <redis_lua.script.Script>` instance.
        :return: An array of regions.
        """
        context = self.ParseRegionsContext()
        lines = content.split('\n')

        # If the file ends with a newline character, the last element will be
        # empty and we don't want it.
        if lines and not lines[-1]:
            lines = lines[:-1]

        for real_line, statement in enumerate(lines, start=1):
            if self._parse_include(
                context,
                real_line,
                statement,
                current_path,
                get_script_by_name,
            ):
                continue

            elif self._parse_key(context, real_line, statement):
                continue

            elif self._parse_arg(context, real_line, statement):
                continue

            else:
                context.add_line(real_line, statement)

        context.normalize()

        return context.regions

    def _parse_include(
        self,
        context,
        real_line,
        statement,
        current_path,
        get_script_by_name,
    ):
        match = re.match(
            r'^\s*%include\s+"(?P<name>[\w\d_\-/\\]+)"\s*$',
            statement,
        )

        if match:
            # We don't want backslashes in script names. Life is already
            # complex enough.
            name = os.path.join(
                current_path,
                match.group('name'),
            ).replace(os.path.sep, '/')
            script = get_script_by_name(name=name)

            context.add_script_region(
                script=script,
                real_line=real_line,
                content=statement,
            )

            return True

    def _parse_key(
        self,
        context,
        real_line,
        statement,
    ):
        match = re.match(
            r'^\s*%key\s+(?P<name>[\w\d_]+)\s*$',
            statement,
        )

        if match:
            name = match.group('name')
            context.add_key_region(
                name=name,
                real_line=real_line,
                content=statement,
            )

            return True

    def _parse_arg(
        self,
        context,
        real_line,
        statement,
    ):
        match = re.match(
            r'^\s*%arg\s+(?P<name>[\w\d_]+)(\s+(?P<type>[\w\d_]+))?\s*$',
            statement,
        )

        if match:
            name = match.group('name')
            type_ = match.group('type')

            try:
                context.add_argument_region(
                    name=name,
                    type_=type_,
                    real_line=real_line,
                    content=statement,
                )
            except ValueError:
                raise ValueError(
                    "Unknown type %r in %r when parsing line %d" % (
                        type_,
                        statement,
                        real_line,
                    ),
                )

            return True

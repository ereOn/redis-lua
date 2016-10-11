"""
Scripts regions.
"""

import os
import re


class ScriptRegion(object):
    def __init__(self, script, content):
        self.script = script
        self.real_line_count = 1
        self.content = content

    def __repr__(self):
        return (
            '{_class}(real_line_count={self.real_line_count}, '
            'line_count={self.line_count}, script=\'{self.script}\', '
            'content={self.content!r})'
        ).format(
            _class=self.__class__.__name__,
            self=self,
        )

    @property
    def line_count(self):
        return self.script.line_count

    def render(self, context):
        return context.render_script(script=self.script)

    def __eq__(self, other):
        if not isinstance(other, ScriptRegion):
            return NotImplemented

        return all([
            other.script == self.script,
            other.content == self.content,
        ])

    @property
    def keys(self):
        return self.script.keys

    @property
    def args(self):
        return self.script.args


class KeyRegion(object):
    def __init__(self, name, index, content):
        self.name = name
        self.index = index
        self.line_count = 1
        self.real_line_count = 1
        self.content = content

    def __repr__(self):
        return (
            '{_class}(line_count={self.line_count}, name=\'{self.name}\', '
            'content={self.content!r})'
        ).format(
            _class=self.__class__.__name__,
            self=self,
        )

    def render(self, context):
        return context.render_key(name=self.name)

    def __eq__(self, other):
        if not isinstance(other, KeyRegion):
            return NotImplemented

        return all([
            other.name == self.name,
            other.index == self.index,
            other.content == self.content,
        ])


class ArgumentRegion(object):
    VALID_TYPES = {
        None: str,
        'int': int,
        'integer': int,
        'string': str,
        'str': str,
        'bool': bool,
        'boolean': bool,
        'dict': dict,
        'dictionary': dict,
        'list': list,
        'array': list,
    }

    @classmethod
    def get_valid_type(cls, type_):
        result = cls.VALID_TYPES.get(type_)

        if result is None:
            raise ValueError("Invalid type '%s' for argument" % type_)

        return result

    def __init__(self, name, index, type_, content):
        self.name = name
        self.index = index
        self.type_ = self.get_valid_type(type_=type_)
        self.line_count = 1
        self.real_line_count = 1
        self.content = content

    def __repr__(self):
        return (
            '{_class}(line_count={self.line_count}, name=\'{self.name}\', '
            'content={self.content!r})'
        ).format(
            _class=self.__class__.__name__,
            self=self,
        )

    def render(self, context):
        return context.render_arg(
            name=self.name,
            type_=self.type_,
        )

    def __eq__(self, other):
        if not isinstance(other, ArgumentRegion):
            return NotImplemented

        return all([
            other.name == self.name,
            other.index == self.index,
            other.type_ == self.type_,
            other.content == self.content,
        ])


class ReturnRegion(object):
    VALID_TYPES = {
        None: str,
        'int': int,
        'integer': int,
        'string': str,
        'str': str,
        'bool': bool,
        'boolean': bool,
        'dict': dict,
        'dictionary': dict,
        'list': list,
        'array': list,
    }

    @classmethod
    def get_valid_type(cls, type_):
        result = cls.VALID_TYPES.get(type_)

        if result is None:
            raise ValueError("Invalid type '%s' for return" % type_)

        return result

    def __init__(self, type_, content):
        self.type_ = self.get_valid_type(type_=type_)
        self.line_count = 1
        self.real_line_count = 1
        self.content = content

    def __repr__(self):
        return '{_class}(line_count={self.line_count})'.format(
            _class=self.__class__.__name__,
            self=self,
        )

    def render(self, context):
        return context.render_return(type_=self.type_)

    def __eq__(self, other):
        if not isinstance(other, ReturnRegion):
            return NotImplemented

        return all([
            other.type_ == self.type_,
            other.content == self.content,
        ])


class PragmaRegion(object):
    VALID_VALUES = {
        'once',
    }

    def __init__(self, value, content):
        if value not in self.VALID_VALUES:
            raise ValueError("Invalid value %r for pragma" % value)

        self.value = value
        self.line_count = 1
        self.real_line_count = 1
        self.content = content

    def __repr__(self):
        return '{_class}(line_count={self.line_count})'.format(
            _class=self.__class__.__name__,
            self=self,
        )

    def render(self, context):
        return context.render_pragma(value=self.value)

    def __eq__(self, other):
        if not isinstance(other, PragmaRegion):
            return NotImplemented

        return all([
            other.value == self.value,
            other.content == self.content,
        ])


class TextRegion(object):
    def __init__(self, content):
        self.content = content
        self.line_count = len(content.split('\n'))
        self.real_line_count = self.line_count

    def __repr__(self):
        return '{_class}(line_count={self.line_count})'.format(
            _class=self.__class__.__name__,
            self=self,
        )

    def render(self, context):
        return context.render_text(text=self.content)

    def __eq__(self, other):
        if not isinstance(other, TextRegion):
            return NotImplemented

        return other.content == self.content


class ScriptParser(object):
    """
    Parse LUA scripts.
    """

    class ParseRegionsContext(object):
        def __init__(self):
            self.regions = []
            self.text_lines = []
            self.key_index = 1
            self.arg_index = 1

        def add_line(self, content):
            self.text_lines.append(content)

        def flush(self):
            if self.text_lines:
                self.regions.append(
                    TextRegion(
                        content='\n'.join(self.text_lines),
                    ),
                )
                self.text_lines = []

        def add_script_region(self, script, content):
            self.flush()

            region = ScriptRegion(
                script=script,
                content=content,
            )
            self.regions.append(region)

            self.key_index += len(script.keys)
            self.arg_index += len(script.args)

        def add_key_region(self, name, content):
            self.flush()

            region = KeyRegion(
                name=name,
                index=self.key_index,
                content=content,
            )
            self.regions.append(region)
            self.key_index += 1

        def add_argument_region(self, name, type_, content):
            self.flush()

            region = ArgumentRegion(
                name=name,
                index=self.arg_index,
                type_=type_,
                content=content,
            )
            self.regions.append(region)
            self.arg_index += 1

        def add_return_region(self, type_, content):
            self.flush()

            region = ReturnRegion(
                type_=type_,
                content=content,
            )
            self.regions.append(region)

        def add_pragma_region(self, value, content):
            self.flush()

            region = PragmaRegion(
                value=value,
                content=content,
            )
            self.regions.append(region)

        def normalize(self):
            self.flush()

            if not self.regions:
                self.add_line('')
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
                statement,
                current_path,
                get_script_by_name,
            ):
                continue

            elif self._parse_key(context, statement):
                continue

            elif self._parse_arg(context, real_line, statement):
                continue

            elif self._parse_return(context, real_line, statement):
                continue

            elif self._parse_pragma(context, real_line, statement):
                continue

            else:
                context.add_line(statement)

        context.normalize()

        return context.regions

    def _parse_include(
        self,
        context,
        statement,
        current_path,
        get_script_by_name,
    ):
        match = re.match(
            r'^\s*%include\s+"(?P<name>[\w\d_\-/\\.]+)"\s*$',
            statement,
        )

        if match:
            # We don't want backslashes in script names. Life is already
            # complex enough.
            name = os.path.relpath(
                os.path.join(
                    current_path,
                    match.group('name'),
                )
            ).replace(os.path.sep, '/')
            script = get_script_by_name(name=name)

            context.add_script_region(
                script=script,
                content=statement,
            )

            return True

    def _parse_key(
        self,
        context,
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

    def _parse_return(
        self,
        context,
        real_line,
        statement,
    ):
        match = re.match(
            r'^\s*%return\s+(?P<type>[\w\d_]+)\s*$',
            statement,
        )

        if match:
            type_ = match.group('type')

            try:
                context.add_return_region(
                    type_=type_,
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

    def _parse_pragma(
        self,
        context,
        real_line,
        statement,
    ):
        match = re.match(
            r'^\s*%pragma\s+(?P<value>[\w\d_]+)\s*$',
            statement,
        )

        if match:
            value = match.group('value')

            try:
                context.add_pragma_region(
                    value=value,
                    content=statement,
                )
            except ValueError:
                raise ValueError(
                    "Unknown value %r in %r when parsing line %d" % (
                        value,
                        statement,
                        real_line,
                    ),
                )

            return True

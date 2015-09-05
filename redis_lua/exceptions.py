"""
Exception classes and error codes.
"""

import re

from contextlib import contextmanager
from redis.exceptions import ResponseError


class ScriptNotFoundError(RuntimeError):
    def __init__(self, name, filename):
        super(ScriptNotFoundError, self).__init__(name, filename)

        self.name = name
        self.filename = filename

    def __str__(self):
        return (
            "No such script '{self.name}' found at '{self.filename}'"
        ).format(self=self)


class CyclicDependencyError(RuntimeError):
    def __init__(self, cycle):
        super(CyclicDependencyError, self).__init__(
            cycle,
        )

        self.cycle = cycle

    def __str__(self):
        return " -> ".join(self.cycle)


class ScriptError(ResponseError):
    def __init__(self, script, line, lua_error, message):
        super(ScriptError, self).__init__(message)
        self.message = message
        self.script = script
        self.line = line
        self.lua_error = lua_error

    def __str__(self):
        result = [
            self.lua_error,
            "LUA Traceback (most recent script last):",
        ]
        scripts_lines = self.script.get_scripts_for_line(self.line)

        for script, line in scripts_lines:
            result.extend(
                [
                    '  Script "{script.name}", line {line}'.format(
                        script=script,
                        line=line,
                    ),
                    "    %s" % script.get_real_line_content(line).strip(),
                ],
            )

        return '\n'.join(result)


def parse_response_error_message(message):
    """
    Parse a ResponseError message.

    :param message: The message to parse.
    :returns: A dict containing the relevant information from the message or
        `None` if the parsing failed.
    """
    match = re.match(
        r'(ERR )?(?P<error>[^:]+): (?P<script>[\w_]+):(?P<line>\d+): '
        '(?P<lua_error>.*)',
        message,
    )

    if match:
        return {
            'error': match.group('error'),
            'script': match.group('script'),
            'line': int(match.group('line')),
            'lua_error': match.group('lua_error'),
        }

    match = re.match(
        r'(?P<error>[^:]+): ([\w@_\(\)]+:\d+): (?P<script>[\w_]+):(?P<line>\d+'
        '): (?P<lua_error>.*)',
        message,
    )

    if match:
        return {
            'error': match.group('error'),
            'script': match.group('script'),
            'line': int(match.group('line')),
            'lua_error': match.group('lua_error'),
        }


@contextmanager
def error_handler(script):
    """
    Wraps LUA script errors into a more human-friendly exception.

    :param script: The top-level script that is being run.
    :yields: The script instance.
    """
    try:
        yield script
    except ResponseError as ex:
        error_info = parse_response_error_message(str(ex))

        if error_info:
            raise ScriptError(
                script=script,
                line=error_info['line'],
                lua_error=error_info['lua_error'],
                message=error_info['error'],
            )

        raise

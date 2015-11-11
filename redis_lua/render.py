"""
Rendering classes and functions.
"""


class RenderContext(object):

    def __init__(self):
        self.rendered_scripts = set()
        self.last_key_index = 0
        self.last_arg_index = 0

    def render_script(self, script):
        if script in self.rendered_scripts:
            return None
        else:
            if not script.multiple_inclusion:
                self.rendered_scripts.add(script)

        return '\n'.join(
            line
            for line in (
                region.render(self)
                for region in script.regions
            )
            if line is not None
        )

    def render_key(self, name):
        self.last_key_index += 1

        return "local {name} = KEYS[{index}]".format(
            name=name,
            index=self.last_key_index,
        )

    def render_arg(self, name, type_):
        self.last_arg_index += 1

        if type_ is int:
            return "local {name} = tonumber(ARGV[{index}])".format(
                name=name,
                index=self.last_arg_index,
            )
        elif type_ is bool:
            return (
                "local {name} = tonumber(ARGV[{index}]) ~= 0"
            ).format(
                name=name,
                index=self.last_arg_index,
            )
        elif type_ in {list, dict}:
            return (
                "local {name} = cjson.decode(ARGV[{index}])"
            ).format(
                name=name,
                index=self.last_arg_index,
            )
        else:
            return "local {name} = ARGV[{index}]".format(
                name=name,
                index=self.last_arg_index,
            )

    def render_return(self, type_):
        return '-- Expected return type is: %r' % type_

    def render_pragma(self, value):
        if value == 'once':
            return '-- File can only be included once.'

        raise AssertionError("Can't render unknown pragma type: %r" % value)

    def render_text(self, text):
        return text

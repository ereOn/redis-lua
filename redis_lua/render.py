"""
Rendering classes and functions.
"""


class RenderContext(object):

    def __init__(self):
        self.rendered_scripts = set()

    def render_script(self, script):
        if script in self.rendered_scripts:
            return None
        else:
            self.rendered_scripts.add(script)

        return '\n'.join(
            line
            for line in (
                region.render(self)
                for region in script.regions
            )
            if line is not None
        )

    def render_key(self, name, index):
        return "local {name} = KEYS[{index}]".format(name=name, index=index)

    def render_arg(self, name, type_, index):
        if type_ is int:
            return "local {name} = tonumber(ARGV[{index}])".format(
                name=name,
                index=index,
            )
        elif type_ is bool:
            return (
                "local {name} = tonumber(ARGV[{index}]) ~= 0"
            ).format(
                name=name,
                index=index,
            )
        elif type_ in {list, dict}:
            return (
                "local {name} = cjson.decode(ARGV[{index}])"
            ).format(
                name=name,
                index=index,
            )
        else:
            return "local {name} = ARGV[{index}]".format(
                name=name,
                index=index,
            )

    def render_return(self, type_):
        return '-- Expected return type is: %r' % type_

    def render_text(self, text):
        return text

from mock import MagicMock
from unittest import TestCase

from redis_lua.render import RenderContext


class RenderContextTests(TestCase):

    def setUp(self):
        self.render_context = RenderContext()

    def test_render_script(self):
        script = MagicMock()
        ok_region = MagicMock()
        ok_region.render.return_value = 'a'
        ko_region = MagicMock()
        ko_region.render.return_value = None

        script.regions = [
            ok_region,
            ko_region,
            ok_region,
        ]
        result = self.render_context.render_script(script=script)

        self.assertEqual('a\na', result)

    def test_render_script_already_rendered(self):
        script = MagicMock()
        ok_region = MagicMock()
        ok_region.render.return_value = 'a'
        ko_region = MagicMock()
        ko_region.render.return_value = None

        script.regions = [
            ok_region,
            ko_region,
            ok_region,
        ]

        # Render the script a first time.
        self.render_context.render_script(script=script)
        result = self.render_context.render_script(script=script)

        self.assertIsNone(result)

    def test_render_key(self):
        result = self.render_context.render_key(
            name='mykey',
            index=7,
        )

        self.assertEqual('local mykey = KEYS[7]', result)

    def test_render_arg_as_int(self):
        result = self.render_context.render_arg(
            name='myarg',
            type_=int,
            index=7,
        )

        self.assertEqual('local myarg = tonumber(ARGV[7])', result)

    def test_render_arg_as_bool(self):
        result = self.render_context.render_arg(
            name='myarg',
            type_=bool,
            index=7,
        )

        self.assertEqual('local myarg = tonumber(ARGV[7]) ~= 0', result)

    def test_render_arg_as_string(self):
        result = self.render_context.render_arg(
            name='myarg',
            type_=str,
            index=7,
        )

        self.assertEqual('local myarg = ARGV[7]', result)

    def test_render_arg_as_list(self):
        result = self.render_context.render_arg(
            name='myarg',
            type_=list,
            index=7,
        )

        self.assertEqual('local myarg = cjson.decode(ARGV[7])', result)

    def test_render_arg_as_dict(self):
        result = self.render_context.render_arg(
            name='myarg',
            type_=dict,
            index=7,
        )

        self.assertEqual('local myarg = cjson.decode(ARGV[7])', result)

    def test_render_return(self):
        result = self.render_context.render_return(
            type_=str,
        )

        self.assertEqual('-- Expected return type is: %r' % str, result)

    def test_render_pragma(self):
        result = self.render_context.render_pragma(
            value='once',
        )

        self.assertEqual('-- File can only be included once.', result)

    def test_render_pragma_unknown(self):
        with self.assertRaises(AssertionError):
            self.render_context.render_pragma(
                value='unknown',
            )

    def test_render_text(self):
        result = self.render_context.render_text(
            text="foo foo foo",
        )

        self.assertEqual('foo foo foo', result)

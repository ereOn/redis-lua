from mock import (
    MagicMock,
    patch,
)
from unittest import TestCase

from redis.client import BasePipeline

from redis_lua.script import (
    Script,
    jdumps,
)
from redis_lua.regions import (
    TextRegion,
    ScriptRegion,
    KeyRegion,
    ArgumentRegion,
    ReturnRegion,
    PragmaRegion,
)


class ObjectsScriptTests(TestCase):

    def test_script_instanciation(self):
        name = 'foo'
        regions = [
            TextRegion(content='a'),
        ]
        script = Script(
            name=name,
            regions=regions,
        )

        self.assertEqual(name, script.name)
        self.assertEqual(regions, script.regions)
        self.assertIsNone(script.return_type)
        self.assertTrue(script.multiple_inclusion)

    def test_script_instanciation_no_regions(self):
        name = 'foo'
        regions = []

        with self.assertRaises(ValueError):
            Script(
                name=name,
                regions=regions,
            )

    def test_script_instanciation_with_keys(self):
        name = 'foo'
        subregions = [
            KeyRegion(
                name="key2",
                index=1,
                content='%key key2',
            ),
            TextRegion(content='local b = 0;'),
        ]
        regions = [
            KeyRegion(
                name="key1",
                index=1,
                content='%key key1',
            ),
            TextRegion(content='a'),
            ScriptRegion(
                script=Script(
                    name='bar',
                    regions=subregions,
                ),
                content='%include "bar"',
            ),
            KeyRegion(
                name="key3",
                index=3,
                content='%key key3',
            ),
        ]
        script = Script(
            name=name,
            regions=regions,
        )

        self.assertEqual(
            [
                "key1",
                "key2",
                "key3",
            ],
            script.keys,
        )

    def test_script_instanciation_with_incorrect_keys(self):
        name = 'foo'
        regions = [
            KeyRegion(
                name="key1",
                index=1,
                content='%key key1',
            ),
            KeyRegion(
                name="key2",
                index=3,
                content='%key key2',
            ),
        ]
        with self.assertRaises(ValueError):
            Script(
                name=name,
                regions=regions,
            )

    def test_script_instanciation_with_args(self):
        name = 'foo'
        subregions = [
            ArgumentRegion(
                name="arg2",
                index=1,
                type_='string',
                content='%arg arg2',
            ),
            TextRegion(content='local b = 0;'),
        ]
        regions = [
            ArgumentRegion(
                name="arg1",
                index=1,
                type_='string',
                content='%arg arg1',
            ),
            TextRegion(content='a'),
            ScriptRegion(
                script=Script(
                    name='bar',
                    regions=subregions,
                ),
                content='%include "bar"',
            ),
            ArgumentRegion(
                name="arg3",
                index=3,
                type_='integer',
                content='%arg arg3 integer',
            ),
        ]
        script = Script(
            name=name,
            regions=regions,
        )

        self.assertEqual(
            [
                ("arg1", str),
                ("arg2", str),
                ("arg3", int),
            ],
            script.args,
        )

    def test_script_instanciation_with_incorrect_args(self):
        name = 'foo'
        regions = [
            ArgumentRegion(
                name="arg1",
                type_='string',
                index=1,
                content='%arg arg1',
            ),
            ArgumentRegion(
                name="arg2",
                type_='string',
                index=3,
                content='%arg arg2',
            ),
        ]
        with self.assertRaises(ValueError):
            Script(
                name=name,
                regions=regions,
            )

    def test_script_instanciation_with_return_statement(self):
        name = 'foo'
        regions = [
            ArgumentRegion(
                name="arg1",
                type_='string',
                index=1,
                content='%arg arg1',
            ),
            ReturnRegion(
                type_='integer',
                content='%return integer',
            ),
        ]
        script = Script(
            name=name,
            regions=regions,
        )

        self.assertIs(int, script.return_type)

    def test_script_instanciation_with_too_many_return_statements(self):
        name = 'foo'
        regions = [
            ReturnRegion(
                type_='string',
                content='%return string',
            ),
            ReturnRegion(
                type_='integer',
                content='%return integer',
            ),
        ]
        with self.assertRaises(ValueError):
            Script(
                name=name,
                regions=regions,
            )

    def test_script_instanciation_with_pragma_once(self):
        name = 'foo'
        regions = [
            PragmaRegion(
                value='once',
                content='%pragma once',
            ),
            ReturnRegion(
                type_='integer',
                content='%return integer',
            ),
        ]
        script = Script(
            name=name,
            regions=regions,
        )

        self.assertFalse(script.multiple_inclusion)

    def test_script_representation(self):
        name = 'foo'
        regions = [
            TextRegion(content='a'),
        ]
        script = Script(
            name=name,
            regions=regions,
        )

        self.assertEqual(
            "Script(name='foo')",
            repr(script),
        )

    def test_script_render(self):
        name = 'foo'
        regions = [
            TextRegion(content='a'),
        ]
        script = Script(
            name=name,
            regions=regions,
        )
        context = MagicMock()
        result = script.render(context=context)

        self.assertEqual(context.render_script.return_value, result)
        context.render_script.assert_called_once_with(script)

    def test_script_render_default(self):
        name = 'foo'
        regions = [
            TextRegion(content='a'),
            TextRegion(content='b'),
            TextRegion(content='c'),
        ]
        script = Script(
            name=name,
            regions=regions,
        )

        self.assertEqual('a\nb\nc', script.render())

        # Make sure a second call (with the cached value) returns the same
        # script.
        self.assertEqual('a\nb\nc', script.render())

    def test_script_render_with_duplicate_includes_nested_keys(self):
        script_a = Script(
            name='a',
            regions=[
                KeyRegion(
                    name='key1',
                    index=1,
                    content='%key key1',
                ),
            ],
        )
        script_b = Script(
            name='b',
            regions=[
                KeyRegion(
                    name='key2',
                    index=1,
                    content='%key key2',
                ),
            ],
        )
        script_c = Script(
            name='c',
            regions=[
                KeyRegion(
                    name='key3',
                    index=1,
                    content='%key key3',
                ),
            ],
        )
        script_d = Script(
            name='d',
            regions=[
                ScriptRegion(
                    script=script_c,
                    content='%include "c"',
                ),
                KeyRegion(
                    name='key4',
                    index=2,
                    content='%key key4',
                ),
            ],
        )
        script = Script(
            name='abcd',
            regions=[
                ScriptRegion(
                    script=script_a,
                    content='%include "a"',
                ),
                ScriptRegion(
                    script=script_b,
                    content='%include "b"',
                ),
                ScriptRegion(
                    script=script_d,
                    content='%include "d"',
                ),
            ],
        )

        self.assertEqual(
            [
                'local key1 = KEYS[1]',
                'local key2 = KEYS[2]',
                'local key3 = KEYS[3]',
                'local key4 = KEYS[4]',
            ],
            script.render().split('\n'),
        )

    def test_script_render_with_duplicate_includes_nested_args(self):
        script_a = Script(
            name='a',
            regions=[
                ArgumentRegion(
                    name='arg1',
                    type_='string',
                    index=1,
                    content='%arg arg1',
                ),
            ],
        )
        script_b = Script(
            name='b',
            regions=[
                ArgumentRegion(
                    name='arg2',
                    type_='string',
                    index=1,
                    content='%arg arg2',
                ),
            ],
        )
        script_c = Script(
            name='c',
            regions=[
                ArgumentRegion(
                    name='arg3',
                    type_='string',
                    index=1,
                    content='%arg arg3',
                ),
            ],
        )
        script_d = Script(
            name='d',
            regions=[
                ScriptRegion(
                    script=script_c,
                    content='%include "c"',
                ),
                ArgumentRegion(
                    name='arg4',
                    type_='string',
                    index=2,
                    content='%arg arg4',
                ),
            ],
        )
        script = Script(
            name='abcd',
            regions=[
                ScriptRegion(
                    script=script_a,
                    content='%include "a"',
                ),
                ScriptRegion(
                    script=script_b,
                    content='%include "b"',
                ),
                ScriptRegion(
                    script=script_d,
                    content='%include "d"',
                ),
            ],
        )

        self.assertEqual(
            [
                'local arg1 = ARGV[1]',
                'local arg2 = ARGV[2]',
                'local arg3 = ARGV[3]',
                'local arg4 = ARGV[4]',
            ],
            script.render().split('\n'),
        )

    def test_script_render_with_duplicate_includes(self):
        subsubscript = Script(
            name='a',
            regions=[
                TextRegion(content='a'),
            ],
        )
        subscript = Script(
            name='b',
            regions=[
                TextRegion(content='b'),
                ScriptRegion(
                    script=subsubscript,
                    content='%include "a"',
                ),
            ],
        )
        script = Script(
            name='c',
            regions=[
                ScriptRegion(
                    script=subsubscript,
                    content='%include "a"',
                ),
                ScriptRegion(
                    script=subscript,
                    content='%include "b"',
                ),
                ScriptRegion(
                    script=subscript,
                    content='%include "b"',
                ),
            ],
        )

        self.assertEqual('a\nb\na\nb\na', script.render())

    def test_script_render_with_duplicate_includes_pragma_once(self):
        subsubscript = Script(
            name='a',
            regions=[
                TextRegion(content='a'),
            ],
        )
        subsubscript.multiple_inclusion = False
        subscript = Script(
            name='b',
            regions=[
                TextRegion(content='b'),
                ScriptRegion(
                    script=subsubscript,
                    content='%include "a"',
                ),
            ],
        )
        subscript.multiple_inclusion = False
        script = Script(
            name='c',
            regions=[
                ScriptRegion(
                    script=subsubscript,
                    content='%include "a"',
                ),
                ScriptRegion(
                    script=subscript,
                    content='%include "b"',
                ),
                ScriptRegion(
                    script=subscript,
                    content='%include "b"',
                ),
            ],
        )
        script.multiple_inclusion = False

        self.assertEqual('a\nb', script.render())

    def test_script_line_count(self):
        name = 'foo'
        regions = [
            TextRegion(content='a'),
            TextRegion(content='b'),
            TextRegion(content='c'),
        ]
        script = Script(
            name=name,
            regions=regions,
        )

        self.assertEqual(3, script.line_count)
        self.assertEqual(3, script.real_line_count)

    def test_script_get_real_line_content(self):
        name = 'foo'
        subregions = [
            TextRegion(content='e\nf\ng'),
        ]
        regions = [
            TextRegion(content='a'),
            TextRegion(content='b'),
            TextRegion(content='c\nd'),
            ScriptRegion(
                script=Script(
                    name='bar',
                    regions=subregions,
                ),
                content='%include "bar"',
            ),
            TextRegion(content='h'),
        ]
        script = Script(
            name=name,
            regions=regions,
        )

        with self.assertRaises(ValueError):
            script.get_real_line_content(0)

        self.assertEqual('a', script.get_real_line_content(1))
        self.assertEqual('b', script.get_real_line_content(2))
        self.assertEqual('c', script.get_real_line_content(3))
        self.assertEqual('d', script.get_real_line_content(4))
        self.assertEqual('%include "bar"', script.get_real_line_content(5))
        self.assertEqual('%include "bar"', script.get_real_line_content(6))
        self.assertEqual('%include "bar"', script.get_real_line_content(7))
        self.assertEqual('h', script.get_real_line_content(8))

        with self.assertRaises(ValueError):
            script.get_real_line_content(9)

    def test_script_get_scripts_for_line(self):
        script_a = Script(
            name='a',
            regions=[
                TextRegion(content='>c\n>d'),
            ],
        )
        script_b = Script(
            name='b',
            regions=[
                TextRegion(content='>f\n>g'),
            ],
        )
        script = Script(
            name='foo',
            regions=[
                TextRegion(content='a'),
                TextRegion(content='b'),
                ScriptRegion(
                    script=script_a,
                    content='%include "a"',
                ),
                TextRegion(content='e'),
                ScriptRegion(
                    script=script_b,
                    content='%include "b"',
                ),
                # Next script inclusion will be ignored as the script was
                # already included.
                # It won't be possible to get an error from this inclusion line
                # so we expect a like skip.
                ScriptRegion(
                    script=script_a,
                    content='%include "a"',
                ),
                TextRegion(content='h\ni\nj'),
            ],
        )

        get_scripts_for_line = script.get_scripts_for_line

        with self.assertRaises(ValueError):
            get_scripts_for_line(0)

        self.assertEqual([(script, 1)], get_scripts_for_line(1))
        self.assertEqual([(script, 2)], get_scripts_for_line(2))
        self.assertEqual([(script, 3), (script_a, 1)], get_scripts_for_line(3))
        self.assertEqual([(script, 3), (script_a, 2)], get_scripts_for_line(4))
        self.assertEqual([(script, 4)], get_scripts_for_line(5))
        self.assertEqual([(script, 5), (script_b, 1)], get_scripts_for_line(6))
        self.assertEqual([(script, 5), (script_b, 2)], get_scripts_for_line(7))
        # Here goes the line skip.
        self.assertEqual([(script, 7)], get_scripts_for_line(8))
        self.assertEqual([(script, 8)], get_scripts_for_line(9))
        self.assertEqual([(script, 9)], get_scripts_for_line(10))

        with self.assertRaises(ValueError):
            get_scripts_for_line(11)

    def test_script_get_line_info(self):
        name = 'foo'
        subregions = [
            TextRegion(content='e\nf\ng'),
        ]
        regions = [
            TextRegion(content='a'),
            TextRegion(content='b'),
            TextRegion(content='c\nd'),
            ScriptRegion(
                script=Script(
                    name='bar',
                    regions=subregions,
                ),
                content='%include "bar"',
            ),
            TextRegion(content='h'),
        ]
        script = Script(
            name=name,
            regions=regions,
        )

        get_line_info = script.get_line_info

        with self.assertRaises(ValueError):
            get_line_info(0)

        self.assertEqual((1, 1, 1, 1, 1, 1, regions[0]), get_line_info(1))
        self.assertEqual((2, 2, 1, 2, 2, 1, regions[1]), get_line_info(2))
        self.assertEqual((3, 3, 2, 3, 3, 2, regions[2]), get_line_info(3))
        self.assertEqual((3, 4, 2, 3, 4, 2, regions[2]), get_line_info(4))
        self.assertEqual((5, 5, 1, 5, 5, 3, regions[3]), get_line_info(5))
        self.assertEqual((5, 5, 1, 5, 6, 3, regions[3]), get_line_info(6))
        self.assertEqual((5, 5, 1, 5, 7, 3, regions[3]), get_line_info(7))
        self.assertEqual((6, 6, 1, 8, 8, 1, regions[4]), get_line_info(8))

        with self.assertRaises(ValueError):
            get_line_info(9)

    def test_script_get_line_info_multiple_includes(self):
        name = 'a'
        c_regions = [
            TextRegion(content='4\n5\n6'),
        ]
        c_script = Script(
            name='c',
            regions=c_regions,
        )
        b_regions = [
            TextRegion(content='1\n2\n3'),
            ScriptRegion(
                script=c_script,
                content='%include "c"',
            ),
        ]
        b_script = Script(
            name='b',
            regions=b_regions,
        )
        a_regions = [
            ScriptRegion(
                script=b_script,
                content='%include "b"',
            ),
            ScriptRegion(
                script=c_script,
                content='%include "c"',
            ),
            ScriptRegion(
                script=c_script,
                content='%include "c"',
            ),
            TextRegion(content='7'),
        ]
        script = Script(
            name=name,
            regions=a_regions,
        )

        get_line_info = script.get_line_info

        with self.assertRaises(ValueError):
            get_line_info(0)

        self.assertEqual((1, 1, 1, 1, 1, 6, a_regions[0]), get_line_info(1))
        self.assertEqual((1, 1, 1, 1, 2, 6, a_regions[0]), get_line_info(2))
        self.assertEqual((1, 1, 1, 1, 3, 6, a_regions[0]), get_line_info(3))
        self.assertEqual((1, 1, 1, 1, 4, 6, a_regions[0]), get_line_info(4))
        self.assertEqual((1, 1, 1, 1, 5, 6, a_regions[0]), get_line_info(5))
        self.assertEqual((1, 1, 1, 1, 6, 6, a_regions[0]), get_line_info(6))
        self.assertEqual((4, 4, 1, 7, 7, 1, a_regions[3]), get_line_info(7))

        with self.assertRaises(ValueError):
            get_line_info(8)

    def test_script_as_string(self):
        name = 'foo'
        regions = [
            TextRegion(content='a'),
        ]
        script = Script(
            name=name,
            regions=regions,
        )

        self.assertEqual('foo.lua', str(script))

    def test_script_equality(self):
        name = 'name'
        regions = [
            TextRegion(content='a'),
        ]
        script_a = Script(
            name=name,
            regions=regions,
        )
        script_b = Script(
            name=name,
            regions=regions,
        )
        script_c = Script(
            name=name + 'different',
            regions=regions,
        )
        script_d = Script(
            name=name,
            regions=regions + regions,
        )

        self.assertTrue(script_a == script_a)
        self.assertTrue(hash(script_a) == hash(script_a))
        self.assertIsNot(script_a, script_b)
        self.assertTrue(script_a == script_b)
        self.assertTrue(hash(script_a) == hash(script_b))
        self.assertFalse(script_a == script_c)
        self.assertFalse(hash(script_a) == hash(script_c))
        self.assertFalse(script_a == script_d)
        self.assertTrue(hash(script_a) == hash(script_d))
        self.assertFalse(script_a == 42)

    @patch('redis_lua.script.RedisScript')
    def test_script_run(self, _):
        name = 'foo'
        regions = [
            KeyRegion(
                name='key1',
                index=1,
                content='%key key1',
            ),
            ArgumentRegion(
                name='arg1',
                index=1,
                type_='string',
                content='%arg arg1',
            ),
            TextRegion(content='b'),
            KeyRegion(
                name='key2',
                index=2,
                content='%key key2',
            ),
            ArgumentRegion(
                name='arg2',
                index=2,
                type_='integer',
                content='%arg arg2',
            ),
            ArgumentRegion(
                name='arg3',
                index=3,
                type_='bool',
                content='%arg arg3',
            ),
            ArgumentRegion(
                name='arg4',
                index=4,
                type_='list',
                content='%arg arg4',
            ),
            ArgumentRegion(
                name='arg5',
                index=5,
                type_='dict',
                content='%arg arg5',
            ),
        ]
        script = Script(
            name=name,
            regions=regions,
        )
        script._redis_scripts[None] = MagicMock(return_value="result")
        result = script.get_runner(client=None)(
            arg1='ARG',
            arg2=2,
            arg3=False,
            arg4=(1, 2.5, None, 'a'),
            arg5={'b': None},
            key1='KEY',
            key2='KEY 2',
        )

        self.assertEqual("result", result)
        script._redis_scripts[None].assert_called_once_with(
            keys=['KEY', 'KEY 2'],
            args=[
                'ARG',
                2,
                0,
                jdumps([1, 2.5, None, 'a']),
                jdumps({'b': None}),
            ],
        )

    @patch('redis_lua.script.RedisScript')
    def test_script_call_in_pipeline(self, redis_script):
        name = 'foo'
        regions = [
            ReturnRegion(
                type_='string',
                content='%return string',
            ),
        ]
        script = Script(
            name=name,
            regions=regions,
        )
        client = MagicMock(spec=BasePipeline)
        redis_script.return_value = MagicMock(return_value=42)
        result = script.get_runner(client=client)()

        self.assertTrue(hasattr(result, '__call__'))
        self.assertEqual("42", result(42))
        redis_script.return_value.assert_called_once_with(
            keys=[],
            args=[],
        )

        # Make sure pipeline instances are not cached.
        self.assertNotIn(client, script._redis_scripts)

    @patch('redis_lua.script.RedisScript')
    def test_script_call_return_as_string(self, _):
        name = 'foo'
        regions = [
            ReturnRegion(
                type_='string',
                content='%return string',
            ),
        ]
        script = Script(
            name=name,
            regions=regions,
        )
        script._redis_scripts[None] = MagicMock(return_value=42)
        result = script.get_runner(client=None)()

        self.assertEqual("42", result)
        script._redis_scripts[None].assert_called_once_with(
            keys=[],
            args=[],
        )

    @patch('redis_lua.script.RedisScript')
    def test_script_call_return_as_integer(self, _):
        name = 'foo'
        regions = [
            ReturnRegion(
                type_='integer',
                content='%return integer',
            ),
        ]
        script = Script(
            name=name,
            regions=regions,
        )
        script._redis_scripts[None] = MagicMock(return_value="42")
        result = script.get_runner(client=None)()

        self.assertEqual(42, result)
        script._redis_scripts[None].assert_called_once_with(
            keys=[],
            args=[],
        )

    @patch('redis_lua.script.RedisScript')
    def test_script_call_return_as_boolean(self, _):
        name = 'foo'
        regions = [
            ReturnRegion(
                type_='boolean',
                content='%return boolean',
            ),
        ]
        script = Script(
            name=name,
            regions=regions,
        )
        script._redis_scripts[None] = MagicMock(return_value=5)
        result = script.get_runner(client=None)()

        self.assertEqual(True, result)
        script._redis_scripts[None].assert_called_once_with(
            keys=[],
            args=[],
        )

    @patch('redis_lua.script.RedisScript')
    def test_script_call_return_as_list(self, _):
        name = 'foo'
        regions = [
            ReturnRegion(
                type_='list',
                content='%return list',
            ),
        ]
        script = Script(
            name=name,
            regions=regions,
        )
        value = [1, 'a', None, 3.5]
        script._redis_scripts[None] = MagicMock(return_value=jdumps(value))
        result = script.get_runner(client=None)()

        self.assertEqual(value, result)
        script._redis_scripts[None].assert_called_once_with(
            keys=[],
            args=[],
        )

    @patch('redis_lua.script.RedisScript')
    def test_script_call_return_as_dict(self, _):
        name = 'foo'
        regions = [
            ReturnRegion(
                type_='list',
                content='%return list',
            ),
        ]
        script = Script(
            name=name,
            regions=regions,
        )
        value = {'a': 1, 'b': 3.5, 'c': None, 'd': ['a', 2], 'e': 's'}
        script._redis_scripts[None] = MagicMock(return_value=jdumps(value))
        result = script.get_runner(client=None)()

        self.assertEqual(value, result)
        script._redis_scripts[None].assert_called_once_with(
            keys=[],
            args=[],
        )

    def test_script_call_missing_key(self):
        name = 'foo'
        regions = [
            KeyRegion(
                name='key1',
                index=1,
                content='%key key1',
            ),
            ArgumentRegion(
                name='arg1',
                index=1,
                type_='string',
                content='%arg arg1',
            ),
        ]
        script = Script(
            name=name,
            regions=regions,
        )

        with self.assertRaises(TypeError):
            script.get_runner(client=None)(arg1='ARG')

    def test_script_call_missing_arg(self):
        name = 'foo'
        regions = [
            KeyRegion(
                name='key1',
                index=1,
                content='%key key1',
            ),
            ArgumentRegion(
                name='arg1',
                index=1,
                type_='string',
                content='%arg arg1',
            ),
        ]
        script = Script(
            name=name,
            regions=regions,
        )

        with self.assertRaises(TypeError):
            script.get_runner(client=None)(key1='KEY')

    def test_script_call_unknown_key_arg(self):
        name = 'foo'
        regions = [
            KeyRegion(
                name='key1',
                index=1,
                content='%key key1',
            ),
            ArgumentRegion(
                name='arg1',
                index=1,
                type_='string',
                content='%arg arg1',
            ),
        ]
        script = Script(
            name=name,
            regions=regions,
        )

        with self.assertRaises(TypeError):
            script.get_runner(client=None)(unknown_key='VALUe')

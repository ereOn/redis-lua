from mock import (
    MagicMock,
    patch,
)
from unittest import TestCase

from redis_lua.script import Script
from redis_lua.regions import (
    TextRegion,
    ScriptRegion,
    KeyRegion,
    ArgumentRegion,
)


class ObjectsScriptTests(TestCase):

    def test_script_instanciation(self):
        name = 'foo'
        regions = [
            TextRegion(content='a', real_line=1, line=1),
        ]
        script = Script(
            name=name,
            regions=regions,
            registered_client=MagicMock(),
        )

        self.assertEqual(name, script.name)
        self.assertEqual(regions, script.regions)

    def test_script_instanciation_no_regions(self):
        name = 'foo'
        regions = []

        with self.assertRaises(ValueError):
            Script(
                name=name,
                regions=regions,
                registered_client=MagicMock(),
            )

    def test_script_instanciation_with_keys(self):
        name = 'foo'
        subregions = [
            KeyRegion(
                name="key2",
                index=1,
                real_line=1,
                line=1,
                content='%key key2',
            ),
            TextRegion(content='local b = 0;', real_line=2, line=2),
        ]
        regions = [
            KeyRegion(
                name="key1",
                index=1,
                real_line=1,
                line=1,
                content='%key key1',
            ),
            TextRegion(content='a', real_line=2, line=2),
            ScriptRegion(
                script=Script(
                    name='bar',
                    regions=subregions,
                    registered_client=MagicMock(),
                ),
                real_line=3,
                line=3,
                content='%include "bar"',
            ),
            KeyRegion(
                name="key3",
                index=3,
                real_line=5,
                line=5,
                content='%key key3',
            ),
        ]
        script = Script(
            name=name,
            regions=regions,
            registered_client=MagicMock(),
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
                real_line=1,
                line=1,
                content='%key key1',
            ),
            KeyRegion(
                name="key2",
                index=3,
                real_line=2,
                line=2,
                content='%key key2',
            ),
        ]
        with self.assertRaises(ValueError):
            Script(
                name=name,
                regions=regions,
                registered_client=MagicMock(),
            )

    def test_script_instanciation_with_args(self):
        name = 'foo'
        subregions = [
            ArgumentRegion(
                name="arg2",
                index=1,
                type_='string',
                real_line=1,
                line=1,
                content='%arg arg2',
            ),
            TextRegion(content='local b = 0;', real_line=2, line=2),
        ]
        regions = [
            ArgumentRegion(
                name="arg1",
                index=1,
                type_='string',
                real_line=1,
                line=1,
                content='%arg arg1',
            ),
            TextRegion(content='a', real_line=2, line=2),
            ScriptRegion(
                script=Script(
                    name='bar',
                    regions=subregions,
                    registered_client=MagicMock(),
                ),
                real_line=3,
                line=3,
                content='%include "bar"',
            ),
            ArgumentRegion(
                name="arg3",
                index=3,
                type_='integer',
                real_line=5,
                line=5,
                content='%arg arg3 integer',
            ),
        ]
        script = Script(
            name=name,
            regions=regions,
            registered_client=MagicMock(),
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
                real_line=1,
                line=1,
                content='%arg arg1',
            ),
            ArgumentRegion(
                name="arg2",
                type_='string',
                index=3,
                real_line=2,
                line=2,
                content='%arg arg2',
            ),
        ]
        with self.assertRaises(ValueError):
            Script(
                name=name,
                regions=regions,
                registered_client=MagicMock(),
            )

    def test_script_representation(self):
        name = 'foo'
        regions = [
            TextRegion(content='a', real_line=1, line=1),
        ]
        script = Script(
            name=name,
            regions=regions,
            registered_client=MagicMock(),
        )

        self.assertEqual(
            "Script(name='foo')",
            repr(script),
        )

    def test_script_content(self):
        name = 'foo'
        regions = [
            TextRegion(content='a', real_line=1, line=1),
            TextRegion(content='b', real_line=2, line=2),
            TextRegion(content='c', real_line=3, line=3),
        ]
        script = Script(
            name=name,
            regions=regions,
            registered_client=MagicMock(),
        )

        self.assertEqual('a\nb\nc', script.content)

    def test_script_line_count(self):
        name = 'foo'
        regions = [
            TextRegion(content='a', real_line=1, line=1),
            TextRegion(content='b', real_line=2, line=2),
            TextRegion(content='c', real_line=3, line=3),
        ]
        script = Script(
            name=name,
            regions=regions,
            registered_client=MagicMock(),
        )

        self.assertEqual(3, script.line_count)
        self.assertEqual(3, script.real_line_count)

    def test_script_get_real_line_content(self):
        name = 'foo'
        subregions = [
            TextRegion(content='e\nf\ng', real_line=1, line=1),
        ]
        regions = [
            TextRegion(content='a', real_line=1, line=1),
            TextRegion(content='b', real_line=2, line=2),
            TextRegion(content='c\nd', real_line=3, line=3),
            ScriptRegion(
                script=Script(
                    name='bar',
                    regions=subregions,
                    registered_client=MagicMock(),
                ),
                real_line=5,
                line=5,
                content='%include "bar"',
            ),
            TextRegion(content='h', real_line=6, line=8),
        ]
        script = Script(
            name=name,
            regions=regions,
            registered_client=MagicMock(),
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
        subscript = Script(
            name='bar',
            regions=[
                TextRegion(content='c\nd', real_line=1, line=1),
            ],
            registered_client=MagicMock(),
        )
        script = Script(
            name='foo',
            regions=[
                TextRegion(content='a', real_line=1, line=1),
                TextRegion(content='b', real_line=2, line=2),
                ScriptRegion(
                    script=subscript,
                    real_line=3,
                    line=3,
                    content='%include "bar"',
                ),
                TextRegion(content='e', real_line=4, line=5),
                ScriptRegion(
                    script=subscript,
                    real_line=5,
                    line=6,
                    content='%include "bar"',
                ),
                TextRegion(content='f\ng\nh', real_line=6, line=8),
            ],
            registered_client=MagicMock(),
        )

        with self.assertRaises(ValueError):
            script.get_scripts_for_line(0)

        self.assertEqual([(script, 1)], script.get_scripts_for_line(1))
        self.assertEqual([(script, 2)], script.get_scripts_for_line(2))
        self.assertEqual(
            [(script, 3), (subscript, 1)],
            script.get_scripts_for_line(3),
        )
        self.assertEqual(
            [(script, 3), (subscript, 2)],
            script.get_scripts_for_line(4),
        )
        self.assertEqual([(script, 4)], script.get_scripts_for_line(5))
        self.assertEqual(
            [(script, 5), (subscript, 1)],
            script.get_scripts_for_line(6),
        )
        self.assertEqual(
            [(script, 5), (subscript, 2)],
            script.get_scripts_for_line(7),
        )
        self.assertEqual([(script, 6)], script.get_scripts_for_line(8))
        self.assertEqual([(script, 7)], script.get_scripts_for_line(9))
        self.assertEqual([(script, 8)], script.get_scripts_for_line(10))

        with self.assertRaises(ValueError):
            script.get_scripts_for_line(11)

    def test_script_get_region_for_line(self):
        name = 'foo'
        subregions = [
            TextRegion(content='e\nf\ng', real_line=1, line=1),
        ]
        regions = [
            TextRegion(content='a', real_line=1, line=1),
            TextRegion(content='b', real_line=2, line=2),
            TextRegion(content='c\nd', real_line=3, line=3),
            ScriptRegion(
                script=Script(
                    name='bar',
                    regions=subregions,
                    registered_client=MagicMock(),
                ),
                real_line=5,
                line=5,
                content='%include "bar"',
            ),
            TextRegion(content='h', real_line=6, line=8),
        ]
        script = Script(
            name=name,
            regions=regions,
            registered_client=MagicMock(),
        )

        with self.assertRaises(ValueError):
            script.get_region_for_line(0)

        self.assertEqual((regions[0], 1), script.get_region_for_line(1))
        self.assertEqual((regions[1], 2), script.get_region_for_line(2))
        self.assertEqual((regions[2], 3), script.get_region_for_line(3))
        self.assertEqual((regions[2], 4), script.get_region_for_line(4))
        self.assertEqual((regions[3], 5), script.get_region_for_line(5))
        self.assertEqual((regions[3], 5), script.get_region_for_line(6))
        self.assertEqual((regions[3], 5), script.get_region_for_line(7))
        self.assertEqual((regions[4], 6), script.get_region_for_line(8))

        with self.assertRaises(ValueError):
            script.get_region_for_line(9)

    def test_script_as_string(self):
        name = 'foo'
        regions = [
            TextRegion(content='a', real_line=1, line=1),
        ]
        script = Script(
            name=name,
            regions=regions,
            registered_client=MagicMock(),
        )

        self.assertEqual('foo.lua', str(script))

    def test_script_equality(self):
        name = 'name'
        regions = [
            TextRegion(content='a', real_line=1, line=1),
        ]
        script_a = Script(
            name=name,
            regions=regions,
            registered_client=MagicMock(),
        )
        script_b = Script(
            name=name,
            regions=regions,
            registered_client=MagicMock(),
        )
        script_c = Script(
            name=name + 'different',
            regions=regions,
            registered_client=MagicMock(),
        )
        script_d = Script(
            name=name,
            regions=regions + [1],
            registered_client=MagicMock(),
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

    def test_script_on_client(self):
        name = 'foo'
        regions = [
            KeyRegion(
                name='key1',
                index=1,
                real_line=1,
                line=1,
                content='%key key1',
            ),
        ]
        script = Script(
            name=name,
            regions=regions,
            registered_client=MagicMock(),
        )
        cloned_script = script.on_client(registered_client=MagicMock())

        self.assertEqual(script, cloned_script)
        self.assertIsNot(script, cloned_script)

    def test_script_on_client_same_client(self):
        name = 'foo'
        regions = [
            KeyRegion(
                name='key1',
                index=1,
                real_line=1,
                line=1,
                content='%key key1',
            ),
        ]
        client = MagicMock()
        script = Script(
            name=name,
            regions=regions,
            registered_client=client,
        )
        cloned_script = script.on_client(registered_client=client)

        self.assertEqual(script, cloned_script)
        self.assertIs(script, cloned_script)

    @patch('redis_lua.script.RedisScript')
    def test_script_call(self, RedisScriptMock):
        name = 'foo'
        regions = [
            KeyRegion(
                name='key1',
                index=1,
                real_line=1,
                line=1,
                content='%key key1',
            ),
            ArgumentRegion(
                name='arg1',
                index=1,
                type_='string',
                real_line=2,
                line=2,
                content='%arg arg1',
            ),
            TextRegion(content='b', real_line=3, line=3),
            KeyRegion(
                name='key2',
                index=2,
                real_line=4,
                line=4,
                content='%key key2',
            ),
            ArgumentRegion(
                name='arg2',
                index=2,
                type_='integer',
                real_line=5,
                line=5,
                content='%arg arg2',
            ),
            ArgumentRegion(
                name='arg3',
                index=3,
                type_='bool',
                real_line=6,
                line=6,
                content='%arg arg3',
            ),
        ]
        script = Script(
            name=name,
            regions=regions,
            registered_client=MagicMock(),
        )
        script.redis_script.return_value = "result"
        result = script(
            arg1='ARG',
            arg2=2,
            arg3=False,
            key1='KEY',
            key2='KEY 2',
        )

        self.assertEqual("result", result)
        script.redis_script.assert_called_once_with(
            client=None,
            keys=['KEY', 'KEY 2'],
            args=['ARG', 2, 0],
        )

    def test_script_call_missing_key(self):
        name = 'foo'
        regions = [
            KeyRegion(
                name='key1',
                index=1,
                real_line=1,
                line=1,
                content='%key key1',
            ),
            ArgumentRegion(
                name='arg1',
                index=1,
                type_='string',
                real_line=2,
                line=2,
                content='%arg arg1',
            ),
        ]
        script = Script(
            name=name,
            regions=regions,
            registered_client=MagicMock(),
        )

        with self.assertRaises(TypeError):
            script(arg1='ARG')

    def test_script_call_missing_arg(self):
        name = 'foo'
        regions = [
            KeyRegion(
                name='key1',
                index=1,
                real_line=1,
                line=1,
                content='%key key1',
            ),
            ArgumentRegion(
                name='arg1',
                index=1,
                type_='string',
                real_line=2,
                line=2,
                content='%arg arg1',
            ),
        ]
        script = Script(
            name=name,
            regions=regions,
            registered_client=MagicMock(),
        )

        with self.assertRaises(TypeError):
            script(key1='KEY')

    def test_script_call_unknown_key_arg(self):
        name = 'foo'
        regions = [
            KeyRegion(
                name='key1',
                index=1,
                real_line=1,
                line=1,
                content='%key key1',
            ),
            ArgumentRegion(
                name='arg1',
                index=1,
                type_='string',
                real_line=2,
                line=2,
                content='%arg arg1',
            ),
        ]
        script = Script(
            name=name,
            regions=regions,
            registered_client=MagicMock(),
        )

        with self.assertRaises(TypeError):
            script(unknown_key='VALUe')

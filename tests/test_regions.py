from functools import partial
from mock import (
    MagicMock,
    call,
)
from unittest import TestCase

from redis_lua.script import Script
from redis_lua.regions import (
    ScriptRegion,
    TextRegion,
    KeyRegion,
    ArgumentRegion,
    ScriptParser,
)


class ScriptRegionTests(TestCase):

    def test_script_region_instanciation(self):
        name = 'foo'
        regions = [
            TextRegion(content='a', real_line=1, line=1),
        ]
        script = Script(
            name=name,
            regions=regions,
            registered_client=MagicMock(),
        )
        line = 7
        script_region = ScriptRegion(
            script=script,
            real_line=line,
            line=line,
            content='%include "foo"',
        )

        self.assertEqual(script, script_region.script)
        self.assertEqual(line, script_region.line)

    def test_script_region_representation(self):
        name = 'foo'
        regions = [
            TextRegion(content='a', real_line=1, line=1),
        ]
        script = Script(
            name=name,
            regions=regions,
            registered_client=MagicMock(),
        )
        line = 7
        script_region = ScriptRegion(
            script=script,
            real_line=line,
            line=line,
            content='%include "foo"',
        )

        self.assertEqual(
            (
                "ScriptRegion(real_line=7, line=7, line_count=1, "
                "script='foo.lua', content='%include \"foo\"')"
            ),
            repr(script_region),
        )

    def test_script_region_line_count(self):
        name = 'foo'
        regions = [
            TextRegion(content='a', real_line=1, line=1),
            TextRegion(content='b', real_line=2, line=2),
        ]
        script = Script(
            name=name,
            regions=regions,
            registered_client=MagicMock(),
        )
        line = 7
        script_region = ScriptRegion(
            script=script,
            real_line=line,
            line=line,
            content='%include "foo"',
        )

        self.assertEqual(script.line_count, script_region.line_count)
        self.assertEqual(1, script_region.real_line_count)

    def test_script_region_keys(self):
        name = 'foo'
        regions = [
            KeyRegion(
                name='key1',
                index=1,
                real_line=1,
                line=1,
                content='%key key1',
            ),
            TextRegion(content='b', real_line=2, line=2),
        ]
        script = Script(
            name=name,
            regions=regions,
            registered_client=MagicMock(),
        )
        line = 7
        script_region = ScriptRegion(
            script=script,
            real_line=line,
            line=line,
            content='%include "foo"',
        )

        self.assertEqual(script.keys, script_region.keys)

    def test_script_region_arguments(self):
        name = 'foo'
        regions = [
            ArgumentRegion(
                name='arg1',
                index=1,
                type_='string',
                real_line=1,
                line=1,
                content='%arg arg1',
            ),
            TextRegion(content='b', real_line=2, line=2),
        ]
        script = Script(
            name=name,
            regions=regions,
            registered_client=MagicMock(),
        )
        line = 7
        script_region = ScriptRegion(
            script=script,
            real_line=line,
            line=line,
            content='%include "foo"',
        )

        self.assertEqual(script.args, script_region.args)

    def test_script_region_as_string(self):
        name = 'foo'
        regions = [
            TextRegion(content='a', real_line=1, line=1),
            TextRegion(content='b', real_line=2, line=2),
        ]
        script = Script(
            name=name,
            regions=regions,
            registered_client=MagicMock(),
        )
        line = 7
        script_region = ScriptRegion(
            script=script,
            real_line=line,
            line=line,
            content='%include "foo"',
        )

        self.assertEqual(script.content, str(script_region))

    def test_script_region_equality(self):
        script = MagicMock(spec=Script)
        other_script = MagicMock(spec=Script)
        line = 7
        script_region_a = ScriptRegion(
            script=script,
            real_line=line,
            line=line,
            content='%include "foo"',
        )
        script_region_b = ScriptRegion(
            script=script,
            real_line=line,
            line=line,
            content='%include "foo"',
        )
        script_region_c = ScriptRegion(
            script=other_script,
            real_line=line,
            line=line,
            content='%include "foo"',
        )
        script_region_d = ScriptRegion(
            script=script,
            real_line=line + 42,
            line=line,
            content='%include "foo"',
        )
        script_region_e = ScriptRegion(
            script=script,
            real_line=line,
            line=line + 42,
            content='%include "foo"',
        )
        script_region_f = ScriptRegion(
            script=script,
            real_line=line,
            line=line,
            content='%include "bar"',
        )

        self.assertIsNot(script_region_a, script_region_b)
        self.assertTrue(script_region_a == script_region_b)
        self.assertFalse(script_region_a == script_region_c)
        self.assertFalse(script_region_a == script_region_d)
        self.assertFalse(script_region_a == script_region_e)
        self.assertFalse(script_region_a == script_region_f)
        self.assertFalse(script_region_a == 42)


class KeyRegionTests(TestCase):

    def test_key_region_instanciation(self):
        name = 'foo'
        index = 1
        line = 7
        key_region = KeyRegion(
            name=name,
            index=index,
            real_line=line,
            line=line,
            content='%key foo',
        )

        self.assertEqual(name, key_region.name)
        self.assertEqual(index, key_region.index)
        self.assertEqual(line, key_region.line)

    def test_key_region_representation(self):
        name = 'foo'
        index = 1
        line = 7
        key_region = KeyRegion(
            name=name,
            index=index,
            real_line=line,
            line=line,
            content='%key foo',
        )

        self.assertEqual(
            (
                "KeyRegion(real_line=7, line=7, line_count=1, "
                "name='foo', content='%key foo')"
            ),
            repr(key_region),
        )

    def test_key_region_line_count(self):
        name = 'foo'
        index = 1
        line = 7
        key_region = KeyRegion(
            name=name,
            index=index,
            real_line=line,
            line=line,
            content='%key foo',
        )

        self.assertEqual(1, key_region.line_count)
        self.assertEqual(1, key_region.real_line_count)

    def test_key_region_as_string(self):
        name = 'foo'
        index = 1
        line = 7
        key_region = KeyRegion(
            name=name,
            index=index,
            real_line=line,
            line=line,
            content='%key foo',
        )

        self.assertEqual("local foo = KEYS[1]", str(key_region))

    def test_key_region_equality(self):
        key_region_a = KeyRegion(
            name="foo",
            index=1,
            real_line=1,
            line=2,
            content='%key foo',
        )
        key_region_b = KeyRegion(
            name="foo",
            index=1,
            real_line=1,
            line=2,
            content='%key foo',
        )
        key_region_c = KeyRegion(
            name="bar",
            index=1,
            real_line=1,
            line=2,
            content='%key foo',
        )
        key_region_d = KeyRegion(
            name="foo",
            index=2,
            real_line=1,
            line=2,
            content='%key foo',
        )
        key_region_e = KeyRegion(
            name="foo",
            index=1,
            real_line=2,
            line=2,
            content='%key foo',
        )
        key_region_f = KeyRegion(
            name="foo",
            index=1,
            real_line=1,
            line=3,
            content='%key foo',
        )
        key_region_g = KeyRegion(
            name="foo",
            index=1,
            real_line=1,
            line=3,
            content='%key bar',
        )

        self.assertIsNot(key_region_a, key_region_b)
        self.assertTrue(key_region_a == key_region_b)
        self.assertFalse(key_region_a == key_region_c)
        self.assertFalse(key_region_a == key_region_d)
        self.assertFalse(key_region_a == key_region_e)
        self.assertFalse(key_region_a == key_region_f)
        self.assertFalse(key_region_a == key_region_g)
        self.assertFalse(key_region_a == 42)


class ArgumentRegionTests(TestCase):

    def test_argument_region_instanciation(self):
        name = 'foo'
        index = 1
        line = 7
        argument_region = ArgumentRegion(
            name=name,
            index=index,
            type_='string',
            real_line=line,
            line=line,
            content='%arg foo',
        )

        self.assertEqual(name, argument_region.name)
        self.assertEqual(index, argument_region.index)
        self.assertEqual(line, argument_region.line)

    def test_argument_region_representation(self):
        name = 'foo'
        index = 1
        line = 7
        argument_region = ArgumentRegion(
            name=name,
            index=index,
            type_='string',
            real_line=line,
            line=line,
            content='%arg foo',
        )

        self.assertEqual(
            (
                "ArgumentRegion(real_line=7, line=7, line_count=1, "
                "name='foo', content='%arg foo')"
            ),
            repr(argument_region),
        )

    def test_argument_region_line_count(self):
        name = 'foo'
        index = 1
        line = 7
        argument_region = ArgumentRegion(
            name=name,
            index=index,
            type_='string',
            real_line=line,
            line=line,
            content='%arg foo',
        )

        self.assertEqual(1, argument_region.line_count)
        self.assertEqual(1, argument_region.real_line_count)

    def test_argument_region_as_string(self):
        name = 'foo'
        index = 1
        line = 7
        argument_region = ArgumentRegion(
            name=name,
            index=index,
            type_='string',
            real_line=line,
            line=line,
            content='%arg foo',
        )

        self.assertEqual("local foo = ARGV[1]", str(argument_region))

    def test_argument_region_as_string_int_type(self):
        name = 'bar'
        index = 2
        line = 7
        argument_region = ArgumentRegion(
            name=name,
            index=index,
            type_='integer',
            real_line=line,
            line=line,
            content='%arg bar',
        )

        self.assertEqual("local bar = tonumber(ARGV[2])", str(argument_region))

    def test_argument_region_as_string_bool_type(self):
        name = 'bar'
        index = 2
        line = 7
        argument_region = ArgumentRegion(
            name=name,
            index=index,
            type_='boolean',
            real_line=line,
            line=line,
            content='%arg bar',
        )

        self.assertEqual(
            "local bar = tonumber(ARGV[2]) ~= 0",
            str(argument_region),
        )

    def test_argument_region_equality(self):
        argument_region_a = ArgumentRegion(
            name="foo",
            index=1,
            type_='string',
            real_line=1,
            line=2,
            content='%arg foo',
        )
        argument_region_b = ArgumentRegion(
            name="foo",
            index=1,
            type_='string',
            real_line=1,
            line=2,
            content='%arg foo',
        )
        argument_region_c = ArgumentRegion(
            name="bar",
            index=1,
            type_='string',
            real_line=1,
            line=2,
            content='%arg foo',
        )
        argument_region_d = ArgumentRegion(
            name="foo",
            index=2,
            type_='string',
            real_line=1,
            line=2,
            content='%arg foo',
        )
        argument_region_e = ArgumentRegion(
            name="foo",
            index=2,
            type_='integer',
            real_line=1,
            line=2,
            content='%arg foo',
        )
        argument_region_f = ArgumentRegion(
            name="foo",
            index=1,
            type_='string',
            real_line=2,
            line=2,
            content='%arg foo',
        )
        argument_region_g = ArgumentRegion(
            name="foo",
            index=1,
            type_='string',
            real_line=1,
            line=3,
            content='%arg foo',
        )
        argument_region_h = ArgumentRegion(
            name="foo",
            index=1,
            type_='string',
            real_line=1,
            line=3,
            content='%arg bar',
        )

        self.assertIsNot(argument_region_a, argument_region_b)
        self.assertTrue(argument_region_a == argument_region_b)
        self.assertFalse(argument_region_a == argument_region_c)
        self.assertFalse(argument_region_a == argument_region_d)
        self.assertFalse(argument_region_a == argument_region_e)
        self.assertFalse(argument_region_a == argument_region_f)
        self.assertFalse(argument_region_a == argument_region_g)
        self.assertFalse(argument_region_a == argument_region_h)
        self.assertFalse(argument_region_a == 42)


class TextRegionTests(TestCase):

    def test_text_region_instanciation(self):
        content = 'a\nb\nc'
        line = 7
        text_region = TextRegion(content=content, real_line=line, line=line)

        self.assertEqual(content, text_region.content)
        self.assertEqual(line, text_region.line)

    def test_text_region_representation(self):
        content = 'a\nb\nc'
        line = 7
        text_region = TextRegion(content=content, real_line=line, line=line)

        self.assertEqual(
            "TextRegion(real_line=7, line=7, line_count=3)",
            repr(text_region),
        )

    def test_text_region_line_count(self):
        content = 'a\nb\nc'
        line = 7
        text_region = TextRegion(content=content, real_line=line, line=line)

        self.assertEqual(3, text_region.line_count)
        self.assertEqual(3, text_region.real_line_count)

    def test_text_region_as_string(self):
        content = 'a\nb\nc'
        line = 7
        text_region = TextRegion(content=content, real_line=line, line=line)

        self.assertEqual(content, str(text_region))

    def test_text_region_equality(self):
        content = 'a\nb\nc'
        line = 7
        text_region_a = TextRegion(content=content, real_line=line, line=line)
        text_region_b = TextRegion(content=content, real_line=line, line=line)
        text_region_c = TextRegion(
            content=content + 'd',
            real_line=line,
            line=line,
        )
        text_region_d = TextRegion(
            content=content,
            real_line=line + 42,
            line=line,
        )
        text_region_e = TextRegion(
            content=content,
            real_line=line,
            line=line + 42,
        )

        self.assertIsNot(text_region_a, text_region_b)
        self.assertTrue(text_region_a == text_region_b)
        self.assertFalse(text_region_a == text_region_c)
        self.assertFalse(text_region_a == text_region_d)
        self.assertFalse(text_region_a == text_region_e)
        self.assertFalse(text_region_a == 42)


class ScriptParserTests(TestCase):
    def setUp(self):
        self.parser = ScriptParser()
        self.ScriptClass = partial(
            Script,
            registered_client=MagicMock(),
        )

    def test_parse_with_empty_script(self):
        name = 'foo'
        content = ""

        script = self.parser.parse(
            name=name,
            content=content,
            script_class=self.ScriptClass,
            get_script_by_name=None,
        )

        self.assertEqual(name, script.name)
        self.assertEqual(content, script.content)
        self.assertEqual(
            [
                TextRegion(content=content, real_line=1, line=1),
            ],
            script.regions,
        )

    def test_parse_with_duplicate_keys(self):
        name = 'foo'
        contents = [
            '%key a',
            '%key a',
        ]
        content = '\n'.join(contents)

        with self.assertRaises(ValueError):
            self.parser.parse(
                name=name,
                content=content,
                script_class=self.ScriptClass,
                get_script_by_name=None,
            )

    def test_parse_with_duplicate_arguments(self):
        name = 'foo'
        contents = [
            '%arg a',
            '%arg a',
        ]
        content = '\n'.join(contents)

        with self.assertRaises(ValueError):
            self.parser.parse(
                name=name,
                content=content,
                script_class=self.ScriptClass,
                get_script_by_name=None,
            )

    def test_parse_with_duplicate_key_argument(self):
        name = 'foo'
        contents = [
            '%key a',
            '%arg a',
        ]
        content = '\n'.join(contents)

        with self.assertRaises(ValueError):
            self.parser.parse(
                name=name,
                content=content,
                script_class=self.ScriptClass,
                get_script_by_name=None,
            )

    def test_parse_regions_text_only(self):
        content = 'local a = 1;\nlocal b = 2;'
        get_script_by_name = MagicMock()
        regions = self.parser.parse_regions(
            content=content,
            current_path=".",
            get_script_by_name=get_script_by_name,
        )

        self.assertEqual(
            [
                TextRegion(content=content, real_line=1, line=1),
            ],
            regions,
        )
        self.assertEqual(2, regions[0].line_count)
        self.assertEqual(2, regions[0].real_line_count)
        self.assertEqual(0, get_script_by_name.call_count)

    def test_extract_regions_include(self):
        contents = [
            'local a = 1;',
            '%include "foo"',
            'local d = 4;',
            '%include "foo"',
            '%include "foo"',
            'local e = 4;',
        ]
        content = '\n'.join(contents)
        script = Script(
            registered_client=MagicMock(),
            name='foo',
            regions=[
                TextRegion(
                    content='local b = 2;\nlocal c = 3;',
                    real_line=1,
                    line=1,
                ),
            ],
        )
        get_script_by_name = MagicMock(return_value=script)
        regions = self.parser.parse_regions(
            content=content,
            current_path=".",
            get_script_by_name=get_script_by_name,
        )

        self.maxDiff = None
        self.assertEqual(
            [
                TextRegion(content=contents[0], real_line=1, line=1),
                ScriptRegion(
                    script=script,
                    real_line=2,
                    line=2,
                    content='%include "foo"',
                ),
                TextRegion(content=contents[2], real_line=3, line=4),
                ScriptRegion(
                    script=script,
                    real_line=4,
                    line=5,
                    content='%include "foo"',
                ),
                ScriptRegion(
                    script=script,
                    real_line=5,
                    line=7,
                    content='%include "foo"',
                ),
                TextRegion(content=contents[5], real_line=6, line=9),
            ],
            regions,
        )
        self.assertEqual(
            [
                call(name="./%s" % script.name),
                call(name="./%s" % script.name),
                call(name="./%s" % script.name),
            ],
            get_script_by_name.mock_calls[:],
        )

    def test_extract_regions_keys(self):
        contents = [
            '%key key1',
            '%include "foo"',
            '%key key3',
        ]
        content = '\n'.join(contents)
        script = Script(
            registered_client=MagicMock(),
            name='foo',
            regions=[
                KeyRegion(
                    name='key2',
                    index=1,
                    real_line=1,
                    line=1,
                    content='%key key2',
                ),
            ],
        )
        get_script_by_name = MagicMock(return_value=script)
        regions = self.parser.parse_regions(
            content=content,
            current_path=".",
            get_script_by_name=get_script_by_name,
        )

        self.maxDiff = None
        self.assertEqual(
            [
                KeyRegion(
                    name='key1',
                    index=1,
                    real_line=1,
                    line=1,
                    content=contents[0],
                ),
                ScriptRegion(
                    script=script,
                    real_line=2,
                    line=2,
                    content='%include "foo"',
                ),
                KeyRegion(
                    name='key3',
                    index=3,
                    real_line=3,
                    line=3,
                    content=contents[2],
                ),
            ],
            regions,
        )

    def test_extract_regions_arguments(self):
        contents = [
            '%arg arg1',
            '%include "foo"',
            '%arg arg3 string',
            '%arg arg4 integer',
            '%arg arg5 boolean',
        ]
        content = '\n'.join(contents)
        script = Script(
            registered_client=MagicMock(),
            name='foo',
            regions=[
                ArgumentRegion(
                    name='arg2',
                    index=1,
                    type_='string',
                    real_line=1,
                    line=1,
                    content='%arg arg2',
                ),
            ],
        )
        get_script_by_name = MagicMock(return_value=script)
        regions = self.parser.parse_regions(
            content=content,
            current_path=".",
            get_script_by_name=get_script_by_name,
        )

        self.maxDiff = None
        self.assertEqual(
            [
                ArgumentRegion(
                    name='arg1',
                    index=1,
                    type_='string',
                    real_line=1,
                    line=1,
                    content=contents[0],
                ),
                ScriptRegion(
                    script=script,
                    real_line=2,
                    line=2,
                    content='%include "foo"',
                ),
                ArgumentRegion(
                    name='arg3',
                    index=3,
                    type_='string',
                    real_line=3,
                    line=3,
                    content=contents[2],
                ),
                ArgumentRegion(
                    name='arg4',
                    index=4,
                    type_='integer',
                    real_line=4,
                    line=4,
                    content=contents[3],
                ),
                ArgumentRegion(
                    name='arg5',
                    index=5,
                    type_='boolean',
                    real_line=5,
                    line=5,
                    content=contents[4],
                ),
            ],
            regions,
        )

    def test_extract_regions_text_last(self):
        contents = [
            '%arg arg1',
            '%include "foo"',
            '%key key2',
            'a',
            'b',
            'c',
        ]
        content = '\n'.join(contents)
        script = Script(
            registered_client=MagicMock(),
            name='foo',
            regions=[
                ArgumentRegion(
                    name='arg2',
                    index=1,
                    type_='string',
                    real_line=1,
                    line=1,
                    content='%arg arg2',
                ),
                KeyRegion(
                    name='key1',
                    index=1,
                    real_line=2,
                    line=2,
                    content='%key key1',
                ),
            ],
        )
        get_script_by_name = MagicMock(return_value=script)
        regions = self.parser.parse_regions(
            content=content,
            current_path=".",
            get_script_by_name=get_script_by_name,
        )

        self.maxDiff = None
        self.assertEqual(
            [
                ArgumentRegion(
                    name='arg1',
                    index=1,
                    type_='string',
                    real_line=1,
                    line=1,
                    content=contents[0],
                ),
                ScriptRegion(
                    script=script,
                    real_line=2,
                    line=2,
                    content='%include "foo"',
                ),
                KeyRegion(
                    name='key2',
                    index=2,
                    real_line=3,
                    line=4,
                    content=contents[2],
                ),
                TextRegion(
                    real_line=4,
                    line=5,
                    content='\n'.join(contents[3:6]),
                ),
            ],
            regions,
        )

    def test_extract_regions_arguments_invalid(self):
        contents = [
            '%arg arg1 unknowntype',
        ]
        content = '\n'.join(contents)

        with self.assertRaises(ValueError) as error:
            self.parser.parse_regions(
                content=content,
                current_path=".",
                get_script_by_name=None,
            )

        self.assertEqual(
            (
                "Unknown type 'unknowntype' in '%arg arg1 unknowntype' when "
                "parsing line 1"
            ),
            str(error.exception),
        )

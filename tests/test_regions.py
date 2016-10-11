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
    ReturnRegion,
    PragmaRegion,
    ScriptParser,
)


class ScriptRegionTests(TestCase):

    def test_script_region_instanciation(self):
        name = 'foo'
        regions = [
            TextRegion(content='a'),
        ]
        script = Script(
            name=name,
            regions=regions,
        )
        script_region = ScriptRegion(
            script=script,
            content='%include "foo"',
        )

        self.assertEqual(script, script_region.script)

    def test_script_region_representation(self):
        name = 'foo'
        regions = [
            TextRegion(content='a'),
        ]
        script = Script(
            name=name,
            regions=regions,
        )
        script_region = ScriptRegion(
            script=script,
            content='%include "foo"',
        )

        self.assertEqual(
            (
                "ScriptRegion(real_line_count=1, line_count=1, "
                "script='foo.lua', content='%include \"foo\"')"
            ),
            repr(script_region),
        )

    def test_script_region_line_count(self):
        name = 'foo'
        regions = [
            TextRegion(content='a'),
            TextRegion(content='b'),
        ]
        script = Script(
            name=name,
            regions=regions,
        )
        script_region = ScriptRegion(
            script=script,
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
                content='%key key1',
            ),
            TextRegion(content='b'),
        ]
        script = Script(
            name=name,
            regions=regions,
        )
        script_region = ScriptRegion(
            script=script,
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
                content='%arg arg1',
            ),
            TextRegion(content='b'),
        ]
        script = Script(
            name=name,
            regions=regions,
        )
        script_region = ScriptRegion(
            script=script,
            content='%include "foo"',
        )

        self.assertEqual(script.args, script_region.args)

    def test_script_region_as_string(self):
        name = 'foo'
        regions = [
            TextRegion(content='a'),
            TextRegion(content='b'),
        ]
        script = Script(
            name=name,
            regions=regions,
        )
        script_region = ScriptRegion(
            script=script,
            content='%include "foo"',
        )
        render_context = MagicMock()
        result = script_region.render(context=render_context)

        render_context.render_script.assert_called_once_with(script=script)
        self.assertEqual(render_context.render_script.return_value, result)

    def test_script_region_equality(self):
        script = MagicMock(spec=Script)
        other_script = MagicMock(spec=Script)
        script_region_a = ScriptRegion(
            script=script,
            content='%include "foo"',
        )
        script_region_b = ScriptRegion(
            script=script,
            content='%include "foo"',
        )
        script_region_c = ScriptRegion(
            script=other_script,
            content='%include "bar"',
        )
        script_region_d = ScriptRegion(
            script=script,
            content='%include "bar"',
        )

        self.assertIsNot(script_region_a, script_region_b)
        self.assertTrue(script_region_a == script_region_b)
        self.assertFalse(script_region_a == script_region_c)
        self.assertFalse(script_region_a == script_region_d)
        self.assertFalse(script_region_a == 42)


class KeyRegionTests(TestCase):

    def test_key_region_instanciation(self):
        name = 'foo'
        index = 1
        key_region = KeyRegion(
            name=name,
            index=index,
            content='%key foo',
        )

        self.assertEqual(name, key_region.name)
        self.assertEqual(index, key_region.index)

    def test_key_region_representation(self):
        name = 'foo'
        index = 1
        key_region = KeyRegion(
            name=name,
            index=index,
            content='%key foo',
        )

        self.assertEqual(
            (
                "KeyRegion(line_count=1, name='foo', content='%key foo')"
            ),
            repr(key_region),
        )

    def test_key_region_line_count(self):
        name = 'foo'
        index = 1
        key_region = KeyRegion(
            name=name,
            index=index,
            content='%key foo',
        )

        self.assertEqual(1, key_region.line_count)
        self.assertEqual(1, key_region.real_line_count)

    def test_key_region_as_string(self):
        name = 'foo'
        index = 1
        key_region = KeyRegion(
            name=name,
            index=index,
            content='%key foo',
        )
        render_context = MagicMock()
        result = key_region.render(context=render_context)

        render_context.render_key.assert_called_once_with(name=name)
        self.assertEqual(render_context.render_key.return_value, result)

    def test_key_region_equality(self):
        key_region_a = KeyRegion(
            name="foo",
            index=1,
            content='%key foo',
        )
        key_region_b = KeyRegion(
            name="foo",
            index=1,
            content='%key foo',
        )
        key_region_c = KeyRegion(
            name="bar",
            index=1,
            content='%key foo',
        )
        key_region_d = KeyRegion(
            name="foo",
            index=2,
            content='%key foo',
        )
        key_region_e = KeyRegion(
            name="foo",
            index=1,
            content='%key bar',
        )

        self.assertIsNot(key_region_a, key_region_b)
        self.assertTrue(key_region_a == key_region_b)
        self.assertFalse(key_region_a == key_region_c)
        self.assertFalse(key_region_a == key_region_d)
        self.assertFalse(key_region_a == key_region_e)
        self.assertFalse(key_region_a == 42)


class ArgumentRegionTests(TestCase):

    def test_argument_region_instanciation(self):
        name = 'foo'
        index = 1
        argument_region = ArgumentRegion(
            name=name,
            index=index,
            type_='string',
            content='%arg foo',
        )

        self.assertEqual(name, argument_region.name)
        self.assertEqual(index, argument_region.index)

    def test_argument_region_invalid_instanciation(self):
        name = 'foo'
        index = 1

        with self.assertRaises(ValueError):
            ArgumentRegion(
                name=name,
                index=index,
                type_='unknown',
                content='%arg foo',
            )

    def test_argument_region_representation(self):
        name = 'foo'
        index = 1
        argument_region = ArgumentRegion(
            name=name,
            index=index,
            type_='string',
            content='%arg foo',
        )

        self.assertEqual(
            "ArgumentRegion(line_count=1, name='foo', content='%arg foo')",
            repr(argument_region),
        )

    def test_argument_region_line_count(self):
        name = 'foo'
        index = 1
        argument_region = ArgumentRegion(
            name=name,
            index=index,
            type_='string',
            content='%arg foo',
        )

        self.assertEqual(1, argument_region.line_count)
        self.assertEqual(1, argument_region.real_line_count)

    def test_argument_region_as_string(self):
        name = 'foo'
        index = 1
        argument_region = ArgumentRegion(
            name=name,
            index=index,
            type_='string',
            content='%arg foo',
        )
        render_context = MagicMock()
        result = argument_region.render(context=render_context)

        render_context.render_arg.assert_called_once_with(
            name=name,
            type_=str,
        )
        self.assertEqual(render_context.render_arg.return_value, result)

    def test_argument_region_as_string_int_type(self):
        name = 'bar'
        index = 2
        argument_region = ArgumentRegion(
            name=name,
            index=index,
            type_='integer',
            content='%arg bar',
        )
        render_context = MagicMock()
        result = argument_region.render(context=render_context)

        render_context.render_arg.assert_called_once_with(
            name=name,
            type_=int,
        )
        self.assertEqual(render_context.render_arg.return_value, result)

    def test_argument_region_as_string_bool_type(self):
        name = 'bar'
        index = 2
        argument_region = ArgumentRegion(
            name=name,
            index=index,
            type_='boolean',
            content='%arg bar',
        )
        render_context = MagicMock()
        result = argument_region.render(context=render_context)

        render_context.render_arg.assert_called_once_with(
            name=name,
            type_=bool,
        )
        self.assertEqual(render_context.render_arg.return_value, result)

    def test_argument_region_equality(self):
        argument_region_a = ArgumentRegion(
            name="foo",
            index=1,
            type_='string',
            content='%arg foo',
        )
        argument_region_b = ArgumentRegion(
            name="foo",
            index=1,
            type_='string',
            content='%arg foo',
        )
        argument_region_c = ArgumentRegion(
            name="bar",
            index=1,
            type_='string',
            content='%arg foo',
        )
        argument_region_d = ArgumentRegion(
            name="foo",
            index=2,
            type_='string',
            content='%arg foo',
        )
        argument_region_e = ArgumentRegion(
            name="foo",
            index=2,
            type_='integer',
            content='%arg foo',
        )
        argument_region_f = ArgumentRegion(
            name="foo",
            index=1,
            type_='string',
            content='%arg bar',
        )

        self.assertIsNot(argument_region_a, argument_region_b)
        self.assertTrue(argument_region_a == argument_region_b)
        self.assertFalse(argument_region_a == argument_region_c)
        self.assertFalse(argument_region_a == argument_region_d)
        self.assertFalse(argument_region_a == argument_region_e)
        self.assertFalse(argument_region_a == argument_region_f)
        self.assertFalse(argument_region_a == 42)


class ReturnRegionTests(TestCase):

    def setUp(self):
        self.render_context = MagicMock()

    def test_return_region_instanciation(self):
        return_region = ReturnRegion(
            type_='string',
            content='%return string',
        )

        self.assertEqual(str, return_region.type_)

    def test_return_region_invalid_instanciation(self):
        with self.assertRaises(ValueError):
            ReturnRegion(
                type_='unknown',
                content='%return string',
            )

    def test_return_region_representation(self):
        return_region = ReturnRegion(
            type_='string',
            content='%return string',
        )

        self.assertEqual(
            (
                "ReturnRegion(line_count=1)"
            ),
            repr(return_region),
        )

    def test_return_region_line_count(self):
        return_region = ReturnRegion(
            type_='string',
            content='%return string',
        )

        self.assertEqual(1, return_region.line_count)
        self.assertEqual(1, return_region.real_line_count)

    def test_return_region_as_string(self):
        return_region = ReturnRegion(
            type_='string',
            content='%return string',
        )
        render_context = MagicMock()
        result = return_region.render(context=render_context)

        render_context.render_return.assert_called_once_with(type_=str)
        self.assertEqual(render_context.render_return.return_value, result)

    def test_return_region_as_string_int_type(self):
        return_region = ReturnRegion(
            type_='integer',
            content='%return integer',
        )
        render_context = MagicMock()
        result = return_region.render(context=render_context)

        render_context.render_return.assert_called_once_with(type_=int)
        self.assertEqual(render_context.render_return.return_value, result)

    def test_return_region_as_string_bool_type(self):
        return_region = ReturnRegion(
            type_='boolean',
            content='%return bool',
        )
        render_context = MagicMock()
        result = return_region.render(context=render_context)

        render_context.render_return.assert_called_once_with(type_=bool)
        self.assertEqual(render_context.render_return.return_value, result)

    def test_return_region_as_string_list_type(self):
        return_region = ReturnRegion(
            type_='list',
            content='%return list',
        )
        render_context = MagicMock()
        result = return_region.render(context=render_context)

        render_context.render_return.assert_called_once_with(type_=list)
        self.assertEqual(render_context.render_return.return_value, result)

    def test_return_region_as_string_dict_type(self):
        return_region = ReturnRegion(
            type_='dict',
            content='%return dict',
        )
        render_context = MagicMock()
        result = return_region.render(context=render_context)

        render_context.render_return.assert_called_once_with(type_=dict)
        self.assertEqual(render_context.render_return.return_value, result)

    def test_return_region_equality(self):
        return_region_a = ReturnRegion(
            type_='string',
            content='%return string',
        )
        return_region_b = ReturnRegion(
            type_='string',
            content='%return string',
        )
        return_region_c = ReturnRegion(
            type_='integer',
            content='%return integer',
        )

        self.assertIsNot(return_region_a, return_region_b)
        self.assertTrue(return_region_a == return_region_b)
        self.assertFalse(return_region_a == return_region_c)
        self.assertFalse(return_region_a == 42)


class PragmaRegionTests(TestCase):

    def setUp(self):
        self.render_context = MagicMock()

    def test_pragma_region_instanciation(self):
        pragma_region = PragmaRegion(
            value='once',
            content='%pragma once',
        )

        self.assertEqual('once', pragma_region.value)

    def test_pragma_region_invalid_instanciation(self):
        with self.assertRaises(ValueError):
            PragmaRegion(
                value='unknown',
                content='%pragma unknown',
            )

    def test_pragma_region_representation(self):
        pragma_region = PragmaRegion(
            value='once',
            content='%pragma once',
        )

        self.assertEqual(
            (
                "PragmaRegion(line_count=1)"
            ),
            repr(pragma_region),
        )

    def test_pragma_region_line_count(self):
        pragma_region = PragmaRegion(
            value='once',
            content='%pragma once',
        )

        self.assertEqual(1, pragma_region.line_count)
        self.assertEqual(1, pragma_region.real_line_count)

    def test_pragma_region_as_string(self):
        pragma_region = PragmaRegion(
            value='once',
            content='%pragma once',
        )
        render_context = MagicMock()
        result = pragma_region.render(context=render_context)

        render_context.render_pragma.assert_called_once_with(value='once')
        self.assertEqual(render_context.render_pragma.return_value, result)

    def test_pragma_region_equality(self):
        pragma_region_a = PragmaRegion(
            value='once',
            content='%pragma once',
        )
        pragma_region_b = PragmaRegion(
            value='once',
            content='%pragma once',
        )
        pragma_region_c = PragmaRegion(
            value='once',
            content='%pragma  once',
        )

        self.assertIsNot(pragma_region_a, pragma_region_b)
        self.assertTrue(pragma_region_a == pragma_region_b)
        self.assertFalse(pragma_region_a == pragma_region_c)
        self.assertFalse(pragma_region_a == 42)


class TextRegionTests(TestCase):

    def test_text_region_instanciation(self):
        content = 'a\nb\nc'
        text_region = TextRegion(content=content)

        self.assertEqual(content, text_region.content)

    def test_text_region_representation(self):
        content = 'a\nb\nc'
        text_region = TextRegion(content=content)

        self.assertEqual(
            "TextRegion(line_count=3)",
            repr(text_region),
        )

    def test_text_region_line_count(self):
        content = 'a\nb\nc'
        text_region = TextRegion(content=content)

        self.assertEqual(3, text_region.line_count)
        self.assertEqual(3, text_region.real_line_count)

    def test_text_region_render(self):
        content = 'a\nb\nc'
        text_region = TextRegion(content=content)
        render_context = MagicMock()
        result = text_region.render(context=render_context)

        render_context.render_text.assert_called_once_with(text=content)
        self.assertEqual(render_context.render_text.return_value, result)

    def test_text_region_equality(self):
        content = 'a\nb\nc'
        text_region_a = TextRegion(content=content)
        text_region_b = TextRegion(content=content)
        text_region_c = TextRegion(content=content + 'd')

        self.assertIsNot(text_region_a, text_region_b)
        self.assertTrue(text_region_a == text_region_b)
        self.assertFalse(text_region_a == text_region_c)
        self.assertFalse(text_region_a == 42)


class ScriptParserTests(TestCase):
    def setUp(self):
        self.parser = ScriptParser()
        self.ScriptClass = Script

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
        self.assertEqual(content, script.render())
        self.assertEqual(
            [
                TextRegion(content=content),
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
                TextRegion(content=content),
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
            '%include "../foo"',
            '%include "./bar/../foo"',
        ]
        content = '\n'.join(contents)
        script = Script(
            name='foo',
            regions=[
                TextRegion(content='local b = 2;\nlocal c = 3;'),
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
                TextRegion(content=contents[0]),
                ScriptRegion(
                    script=script,
                    content='%include "foo"',
                ),
                TextRegion(content=contents[2]),
                ScriptRegion(
                    script=script,
                    content='%include "foo"',
                ),
                ScriptRegion(
                    script=script,
                    content='%include "foo"',
                ),
                TextRegion(content=contents[5]),
                ScriptRegion(
                    script=script,
                    content='%include "../foo"',
                ),
                ScriptRegion(
                    script=script,
                    content='%include "./bar/../foo"',
                ),
            ],
            regions,
        )
        self.assertEqual(
            [
                call(name="%s" % script.name),
                call(name="%s" % script.name),
                call(name="%s" % script.name),
                call(name="../%s" % script.name),
                call(name="%s" % script.name),
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
            name='foo',
            regions=[
                KeyRegion(
                    name='key2',
                    index=1,
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
                    content=contents[0],
                ),
                ScriptRegion(
                    script=script,
                    content='%include "foo"',
                ),
                KeyRegion(
                    name='key3',
                    index=3,
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
            name='foo',
            regions=[
                ArgumentRegion(
                    name='arg2',
                    index=1,
                    type_='string',
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
                    content=contents[0],
                ),
                ScriptRegion(
                    script=script,
                    content='%include "foo"',
                ),
                ArgumentRegion(
                    name='arg3',
                    index=3,
                    type_='string',
                    content=contents[2],
                ),
                ArgumentRegion(
                    name='arg4',
                    index=4,
                    type_='integer',
                    content=contents[3],
                ),
                ArgumentRegion(
                    name='arg5',
                    index=5,
                    type_='boolean',
                    content=contents[4],
                ),
            ],
            regions,
        )

    def test_extract_regions_return(self):
        contents = [
            '%include "foo"',
            '%return integer',
        ]
        content = '\n'.join(contents)
        script = Script(
            name='foo',
            regions=[
                ReturnRegion(
                    type_='string',
                    content='%return string',
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
                ScriptRegion(
                    script=script,
                    content='%include "foo"',
                ),
                ReturnRegion(
                    type_='integer',
                    content=contents[1],
                ),
            ],
            regions,
        )

    def test_extract_regions_pragma(self):
        contents = [
            '%include "foo"',
            '%pragma once',
        ]
        content = '\n'.join(contents)
        script = Script(
            name='foo',
            regions=[
                PragmaRegion(
                    value='once',
                    content='%pragma once',
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
                ScriptRegion(
                    script=script,
                    content='%include "foo"',
                ),
                PragmaRegion(
                    value='once',
                    content=contents[1],
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
            name='foo',
            regions=[
                ArgumentRegion(
                    name='arg2',
                    index=1,
                    type_='string',
                    content='%arg arg2',
                ),
                KeyRegion(
                    name='key1',
                    index=1,
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
                    content=contents[0],
                ),
                ScriptRegion(
                    script=script,
                    content='%include "foo"',
                ),
                KeyRegion(
                    name='key2',
                    index=2,
                    content=contents[2],
                ),
                TextRegion(content='\n'.join(contents[3:6])),
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

    def test_extract_regions_return_invalid(self):
        contents = [
            '%return unknowntype',
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
                "Unknown type 'unknowntype' in '%return unknowntype' when "
                "parsing line 1"
            ),
            str(error.exception),
        )

    def test_extract_regions_pragma_invalid(self):
        contents = [
            '%pragma unknown',
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
                "Unknown value 'unknown' in '%pragma unknown' when "
                "parsing line 1"
            ),
            str(error.exception),
        )

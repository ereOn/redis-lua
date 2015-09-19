# coding=utf-8

import os
import six

from mock import (
    ANY,
    MagicMock,
    patch,
)
from nose.tools import (
    assert_equal,
    assert_in,
    assert_is,
    assert_raises,
    assert_not_equal,
)

from redis_lua import (
    load_all_scripts,
    load_script,
    load_scripts,
    parse_script,
    read_script,
    run_code,
)
from redis_lua.exceptions import (
    CyclicDependencyError,
    ScriptNotFoundError,
)
from redis_lua.regions import (
    TextRegion,
)
from redis_lua.script import Script

LUA_SEARCH_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    'fixtures',
)


def test_load_all_scripts_no_cache():
    scripts = load_all_scripts(path=LUA_SEARCH_PATH)

    assert_equal(
        {
            'error': ANY,
            'json': ANY,
            'sum': ANY,
            'unicode': ANY,
            'subdir/a': ANY,
            'subdir/b': ANY,
        },
        scripts,
    )


def test_load_all_scripts_cache():
    cache = {}
    scripts = load_all_scripts(
        path=LUA_SEARCH_PATH,
        cache=cache,
    )

    assert_equal(
        {
            'error': ANY,
            'json': ANY,
            'sum': ANY,
            'unicode': ANY,
            'subdir/a': ANY,
            'subdir/b': ANY,
        },
        scripts,
    )
    assert_not_equal({}, cache)


def test_load_scripts_no_cache():
    names = ['sum', 'unicode']
    scripts = load_scripts(
        names=names,
        path=LUA_SEARCH_PATH,
    )

    assert_equal(set(names), {script.name for script in scripts.values()})
    assert_equal(set(names), set(scripts.keys()))


def test_load_scripts_cache_hit():
    names = ['sum', 'foo']
    cache = {
        'foo': Script(
            name='foo',
            regions=[TextRegion(content='')],
        ),
    }
    scripts = load_scripts(
        names=names,
        path=LUA_SEARCH_PATH,
        cache=cache,
    )

    assert_equal(set(names), {script.name for script in scripts.values()})
    assert_equal(set(names), set(scripts.keys()))
    assert_equal(
        {
            'sum': scripts['sum'],
            'foo': scripts['foo'],
        },
        cache,
    )


def test_load_script_no_cache():
    name = 'sum'
    script = load_script(
        name=name,
        path=LUA_SEARCH_PATH,
    )

    assert_equal(name, script.name)


def test_load_script_cache_miss():
    name = 'sum'
    cache = {}
    script = load_script(
        name=name,
        path=LUA_SEARCH_PATH,
        cache=cache,
    )

    assert_equal(name, script.name)
    assert_equal({name: script}, cache)


def test_load_script_cache_hit():
    name = 'sum'
    cache = {
        name: MagicMock(spec=Script),
    }
    script = load_script(
        name=name,
        path=LUA_SEARCH_PATH,
        cache=cache,
    )

    assert_is(cache[name], script)


def test_read_script():
    with open(os.path.join(LUA_SEARCH_PATH, 'sum.lua')) as _file:
        reference_content = _file.read()

    content, path = read_script(name='sum', path=LUA_SEARCH_PATH)

    assert_equal(reference_content, content)
    assert_equal(LUA_SEARCH_PATH, path)


def test_read_script_unicode():
    if six.PY2:
        with open(
            os.path.join(LUA_SEARCH_PATH, 'unicode.lua'),
        ) as _file:
            reference_content = _file.read().decode('utf-8')
    else:
        with open(
            os.path.join(LUA_SEARCH_PATH, 'unicode.lua'),
            encoding='utf-8',
        ) as _file:
            reference_content = _file.read()

    content, path = read_script(
        name='unicode',
        path=LUA_SEARCH_PATH,
        encoding='utf-8',
    )

    assert_equal(reference_content, content)
    assert_equal(LUA_SEARCH_PATH, path)
    assert_in(u'éléphant', content)


def test_read_script_non_existing_file():
    name = 'non_existing_script'

    with assert_raises(ScriptNotFoundError) as error:
        read_script(name=name, path=LUA_SEARCH_PATH)

    assert_equal(name, error.exception.name)
    assert_equal(
        os.path.join(LUA_SEARCH_PATH, name + '.lua'),
        error.exception.filename,
    )


@patch('redis_lua.ScriptParser.parse')
def test_parse_script_no_cache(parse_mock):
    name = 'foo'
    content = ""

    script = parse_script(
        name=name,
        content=content,
    )

    assert_is(parse_mock.return_value, script)
    parse_mock.assert_called_once_with(
        name=name,
        content=content,
        script_class=ANY,
        get_script_by_name=ANY,
    )


@patch('redis_lua.ScriptParser.parse')
def test_parse_script_with_empty_cache(parse_mock):
    name = 'foo'
    content = ""
    cache = {}
    script = parse_script(
        name=name,
        content=content,
        cache=cache,
    )

    assert_is(parse_mock.return_value, script)
    parse_mock.assert_called_once_with(
        name=name,
        content=content,
        script_class=ANY,
        get_script_by_name=ANY,
    )
    assert_equal({name: parse_mock.return_value}, cache)


@patch('redis_lua.ScriptParser.parse')
def test_parse_script_with_existing_cache(parse_mock):
    name = 'foo'
    content = ""
    cache = {name: object()}
    script = parse_script(
        name=name,
        content=content,
        cache=cache,
    )

    assert_is(parse_mock.return_value, script)
    parse_mock.assert_called_once_with(
        name=name,
        content=content,
        script_class=ANY,
        get_script_by_name=ANY,
    )
    assert_equal({name: parse_mock.return_value}, cache)


@patch('redis_lua.ScriptParser.parse')
def test_parse_script_cyclic_dependency(parse_mock):
    name = 'foo'
    content = ""
    ancestors = ['bar', 'foo', 'joo']

    with assert_raises(CyclicDependencyError) as error:
        parse_script(
            name=name,
            content=content,
            ancestors=ancestors,
        )

    assert_equal(error.exception.cycle, ['foo', 'joo', 'foo'])


def test_run_code():
    client = MagicMock()
    result = run_code(
        client=client,
        content="""
        %include "sum"
        return sum(3, 4);
        """,
        path=LUA_SEARCH_PATH,
    )
    assert_equal(client.evalsha(), result)


def test_run_code_with_args():
    client = MagicMock()
    result = run_code(
        client=client,
        content="""
        %arg a int
        %arg b int
        %include "sum"
        return sum(a, b);
        """,
        path=LUA_SEARCH_PATH,
        kwargs={'a': 1, 'b': 2},
    )
    assert_equal(client.evalsha(), result)

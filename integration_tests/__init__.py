import os

from functools import wraps
from nose.tools import (
    assert_equal,
    assert_raises,
)
from nose.plugins.skip import SkipTest

from redis import Redis

try:
    from redis.exceptions import TimeoutError
except ImportError:
    # pyredis is too old: let's fake TimeoutError
    TimeoutError = Exception

try:
    from redis.exceptions import ConnectionError
except ImportError:
    # pyredis is too old: let's fake ConnectionError
    ConnectionError = Exception

from redis_lua import (
    run_code,
    parse_script,
)
from redis_lua.exceptions import ScriptError


REDIS_HOST = os.environ.get('REDIS_HOST', None)
REDIS_PORT = int(os.environ.get('REDIS_PORT', '6379'))
REDIS_DB = int(os.environ.get('REDIS_DB', '0'))
REDIS_PASSWORD = os.environ.get('REDIS_PASSWORD', '')
HAS_REDIS = REDIS_HOST is not None

if HAS_REDIS:
    kwargs = {}

    if TimeoutError is not Exception:
        kwargs.update({
            'socket_connect_timeout': 1,
        })

    REDIS = Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        db=REDIS_DB,
        password=REDIS_PASSWORD,
        socket_timeout=1,
        **kwargs
    )

    try:
        REDIS.ping()
    except (TimeoutError, ConnectionError):
        REDIS = None


def skip_if_no_redis(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not HAS_REDIS:
            raise SkipTest("No Redis server detected.")
        elif not REDIS:
            raise SkipTest(
                "Unable to connect to the Redis server at %s:%s" % (
                    REDIS_HOST,
                    REDIS_PORT,
                ),
            )

        REDIS.flushdb()

        return func(*args, redis=REDIS, **kwargs)

    return wrapper


@skip_if_no_redis
def test_sum(redis):
    result = run_code(
        client=redis,
        content="""
        %arg a integer
        %arg b integer

        return a + b;
        """,
        kwargs={
            'a': 3,
            'b': 4,
        },
    )

    assert_equal(7, result)


@skip_if_no_redis
def test_sum_pipeline(redis):
    with redis.pipeline() as pipeline:
        result = run_code(
            client=pipeline,
            content="""
            %arg a integer
            %arg b integer
            %return string

            return a + b;
            """,
            kwargs={
                'a': 3,
                'b': 4,
            },
        )
        values = pipeline.execute()

    assert_equal([7], values)
    assert_equal("7", result(values[0]))


@skip_if_no_redis
def test_script_error(redis):
    with assert_raises(ScriptError) as error:
        run_code(
            client=redis,
            content="""
            local a = 1;
            local b = 2;
            c = 3; -- This is line 4.
            local d = 4;
            """,
        )

    assert_equal(4, error.exception.line)


@skip_if_no_redis
def test_argument_types(redis):
    args = {
        's': 'foo',
        'i': 42,
        'b': False,
        'l': [1, 2, 'b', None, '5', 3.14],
        'd': {'a': 'alpha', 'b': 5, 'c': None, 'd': 2.45},
    }
    result = run_code(
        client=redis,
        content="""
        %arg s string
        %arg i integer
        %arg b boolean
        %arg l list
        %arg d dict
        %return dict

        return cjson.encode({
            s=s,
            i=i,
            b=b,
            l=l,
            d=d,
        })
        """,
        kwargs=args,
    )

    assert_equal(args, result)


@skip_if_no_redis
def test_doc_example(redis):
    result = run_code(
        client=redis,
        content="""
%arg size integer
%arg members list
%return dict

local foo_id = redis.call('INCR', 'foo:last_id')
local foo_root_key = string.format('foo:%s', foo_id)
local foo_members_key = foo_root_key .. ':members'
local foo_size_key = foo_root_key .. ':size'

redis.call('SET', foo_size_key, size)
redis.call('SADD', foo_members_key, unpack(members))

return cjson.encode({
    id=foo_id,
    members=members,
    size=size,
})
""".strip(),
        kwargs={
            'members': {'john', 'susan', 'bob'},
            'size': 5,
        },
    )

    # This transformation makes the result more easily comparable.
    result['members'] = set(result['members'])

    assert_equal(
        {
            'id': 1,
            'members': {'john', 'susan', 'bob'},
            'size': 5,
        },
        result,
    )


@skip_if_no_redis
def test_multiple_inclusion(redis):
    cache = {}
    parse_script(
        name='a',
        content="""
redis.call('INCR', key_a)
""".strip(),
        cache=cache,
    )
    parse_script(
        name='b',
        content="""
%pragma once
redis.call('INCR', key_b)
""".strip(),
        cache=cache,
    )
    result = run_code(
        client=redis,
        content="""
%key key_a
%key key_b
%include "a"
%include "b"
%include "a"
%include "b"
%return dict

local a = tonumber(redis.call('GET', key_a))
local b = tonumber(redis.call('GET', key_b))

return cjson.encode({
    a=a,
    b=b,
})
""".strip(),
        kwargs={
            'key_a': 'key_a',
            'key_b': 'key_b',
        },
        cache=cache,
    )

    assert_equal(
        {
            'a': 2,
            'b': 1,
        },
        result,
    )

import os

from functools import wraps
from nose.tools import (
    assert_equal,
    assert_raises,
)
from nose.plugins.skip import SkipTest

from redis import Redis
from redis_lua import run_code
from redis_lua.exceptions import ScriptError


REDIS_HOST = os.environ.get('REDIS_HOST', None)
REDIS_PORT = int(os.environ.get('REDIS_PORT', '6379'))
REDIS_DB = int(os.environ.get('REDIS_DB', '0'))
REDIS_PASSWORD = os.environ.get('REDIS_PASSWORD', '')
HAS_REDIS = REDIS_HOST is not None

if HAS_REDIS:
    REDIS = Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        db=REDIS_DB,
        password=REDIS_PASSWORD,
    )


def skip_if_no_redis(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not HAS_REDIS:
            raise SkipTest("No Redis server detected.")

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

local key1 = KEYS[1]
local key2 = KEYS[2]
local arg1 = tonumber(ARGV[1])
local arg2 = not not ARGV[2]

return cjson.encode({
    key1=key1,
    key2=key2,
    arg1=arg1,
    arg2=arg2,
})

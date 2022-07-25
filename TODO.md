# TODO

- 看下uvicorn参数
- 添加更多测试 如会产生错误的测试 多文件支持测试 复杂案例测试等
- 写GitHub或者THUgit的CI测试文件

## pyDigitalWaveTools有问题



cat reference.vcd 
$date
	Mon Jul 25 11:41:57 2022
$end
$version
	Icarus Verilog
$end
$timescale
	1s
$end
$scope module testbench $end
$var wire 1 ! out $end
$var reg 1 " a $end
$var reg 1 # b $end
$scope module myXnor $end
$var wire 1 " a $end
$var wire 1 # b $end
$var wire 1 ! out $end
$upscope $end
$upscope $end
$enddefinitions $end
#0
$dumpvars
x#
x"
x!
$end
#1
1!
0#
0"
#2
0!
1"
#3
1#
0"
#4
1!
1"

cat student.vcd
$date
	Mon Jul 25 11:41:57 2022
$end
$version
	Icarus Verilog
$end
$timescale
	1s
$end
$scope module testbench $end
$var wire 1 ! out $end
$var reg 1 " a $end
$var reg 1 # b $end
$scope module myXnor $end
$var wire 1 " a $end
$var wire 1 # b $end
$var wire 1 ! out $end
$upscope $end
$upscope $end
$enddefinitions $end
#0
$dumpvars
x#
x"
x!
$end
#1
1!
0#
0"
#2
0!
1"
#3
1#
0"
#4
1!
1"

## 输出

INFO:     172.26.0.2:45248 - "POST / HTTP/1.1" 500 Internal Server Error
ERROR:    Exception in ASGI application
Traceback (most recent call last):
  File "/usr/local/lib/python3.8/dist-packages/uvicorn/protocols/http/httptools_impl.py", line 401, in run_asgi
    result = await app(self.scope, self.receive, self.send)
  File "/usr/local/lib/python3.8/dist-packages/uvicorn/middleware/proxy_headers.py", line 78, in __call__
    return await self.app(scope, receive, send)
  File "/usr/local/lib/python3.8/dist-packages/fastapi/applications.py", line 269, in __call__
    await super().__call__(scope, receive, send)
  File "/usr/local/lib/python3.8/dist-packages/starlette/applications.py", line 124, in __call__
    await self.middleware_stack(scope, receive, send)
  File "/usr/local/lib/python3.8/dist-packages/starlette/middleware/errors.py", line 184, in __call__
    raise exc
  File "/usr/local/lib/python3.8/dist-packages/starlette/middleware/errors.py", line 162, in __call__
    await self.app(scope, receive, _send)
  File "/usr/local/lib/python3.8/dist-packages/starlette/exceptions.py", line 93, in __call__
    raise exc
  File "/usr/local/lib/python3.8/dist-packages/starlette/exceptions.py", line 82, in __call__
    await self.app(scope, receive, sender)
  File "/usr/local/lib/python3.8/dist-packages/fastapi/middleware/asyncexitstack.py", line 21, in __call__
    raise e
  File "/usr/local/lib/python3.8/dist-packages/fastapi/middleware/asyncexitstack.py", line 18, in __call__
    await self.app(scope, receive, send)
  File "/usr/local/lib/python3.8/dist-packages/starlette/routing.py", line 670, in __call__
    await route.handle(scope, receive, send)
  File "/usr/local/lib/python3.8/dist-packages/starlette/routing.py", line 266, in handle
    await self.app(scope, receive, send)
  File "/usr/local/lib/python3.8/dist-packages/starlette/routing.py", line 65, in app
    response = await func(request)
  File "/usr/local/lib/python3.8/dist-packages/fastapi/routing.py", line 227, in app
    raw_response = await run_endpoint_function(
  File "/usr/local/lib/python3.8/dist-packages/fastapi/routing.py", line 162, in run_endpoint_function
    return await run_in_threadpool(dependant.call, **values)
  File "/usr/local/lib/python3.8/dist-packages/starlette/concurrency.py", line 41, in run_in_threadpool
    return await anyio.to_thread.run_sync(func, *args)
  File "/usr/local/lib/python3.8/dist-packages/anyio/to_thread.py", line 31, in run_sync
    return await get_asynclib().run_sync_in_worker_thread(
  File "/usr/local/lib/python3.8/dist-packages/anyio/_backends/_asyncio.py", line 937, in run_sync_in_worker_thread
    return await future
  File "/usr/local/lib/python3.8/dist-packages/anyio/_backends/_asyncio.py", line 867, in run
    result = context.run(func, *args)
  File "/app/./main.py", line 497, in judge_student_code
    cmpr = VcdComparator(
  File "/app/./main.py", line 107, in __init__
    vcd.parse(vcd_ref_file)
  File "/app/pyDigitalWaveTools/pyDigitalWaveTools/vcd/parser.py", line 122, in parse
    self.keyword_dispatch[token[1]](tokeniser, token[1])
  File "/app/pyDigitalWaveTools/pyDigitalWaveTools/vcd/parser.py", line 203, in vcd_var
    assert vcdId not in self.idcode2series
AssertionError

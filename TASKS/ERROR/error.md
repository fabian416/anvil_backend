025-11-26 20:56:02.592] get_main_async_session provider:61 DEBUG    - Closing async session.
ERROR:    Exception in ASGI application
  + Exception Group Traceback (most recent call last):
  |   File "/Users/jhordanandresasprillasolis/Documents/GitHub/complete-anvil/anvil_backend/env/lib/python3.12/site-packages/uvicorn/protocols/http/h11_impl.py", line 403, in run_asgi
  |     result = await app(  # type: ignore[func-returns-value]
  |              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  |   File "/Users/jhordanandresasprillasolis/Documents/GitHub/complete-anvil/anvil_backend/env/lib/python3.12/site-packages/uvicorn/middleware/proxy_headers.py", line 60, in __call__
  |     return await self.app(scope, receive, send)
  |            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  |   File "/Users/jhordanandresasprillasolis/Documents/GitHub/complete-anvil/anvil_backend/env/lib/python3.12/site-packages/fastapi/applications.py", line 1054, in __call__
  |     await super().__call__(scope, receive, send)
  |   File "/Users/jhordanandresasprillasolis/Documents/GitHub/complete-anvil/anvil_backend/env/lib/python3.12/site-packages/starlette/applications.py", line 113, in __call__
  |     await self.middleware_stack(scope, receive, send)
  |   File "/Users/jhordanandresasprillasolis/Documents/GitHub/complete-anvil/anvil_backend/env/lib/python3.12/site-packages/starlette/middleware/errors.py", line 186, in __call__
  |     raise exc
  |   File "/Users/jhordanandresasprillasolis/Documents/GitHub/complete-anvil/anvil_backend/env/lib/python3.12/site-packages/starlette/middleware/errors.py", line 164, in __call__
  |     await self.app(scope, receive, _send)
  |   File "/Users/jhordanandresasprillasolis/Documents/GitHub/complete-anvil/anvil_backend/env/lib/python3.12/site-packages/dishka/integrations/starlette.py", line 63, in __call__
  |     async with request.app.state.dishka_container(
  |                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  |   File "/Users/jhordanandresasprillasolis/Documents/GitHub/complete-anvil/anvil_backend/env/lib/python3.12/site-packages/dishka/async_container.py", line 254, in __aexit__
  |     await self.container.close(exception=exc_val)
  |   File "/Users/jhordanandresasprillasolis/Documents/GitHub/complete-anvil/anvil_backend/env/lib/python3.12/site-packages/dishka/async_container.py", line 238, in close
  |     raise ExitError("Cleanup context errors", errors)  # noqa: TRY003
  |     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  | dishka.exceptions.ExitError: Cleanup context errors (2 sub-exceptions)
  +-+---------------- 1 ----------------
    | Traceback (most recent call last):
    |   File "/Users/jhordanandresasprillasolis/Documents/GitHub/complete-anvil/anvil_backend/env/lib/python3.12/site-packages/dishka/async_container.py", line 222, in close
    |     await exit_generator.callable.asend(exception)  # type: ignore[attr-defined]
    |     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    |   File "/Users/jhordanandresasprillasolis/Documents/GitHub/complete-anvil/anvil_backend/src/app/infrastructure/persistence_sqla/provider.py", line 69, in get_auth_async_session
    |     async with async_session_factory() as session:
    |                ^^^^^^^^^^^^^^^^^^^^^^^
    |   File "/Users/jhordanandresasprillasolis/Documents/GitHub/complete-anvil/anvil_backend/env/lib/python3.12/site-packages/sqlalchemy/ext/asyncio/session.py", line 1085, in __aexit__
    |     await asyncio.shield(task)
    |   File "/Users/jhordanandresasprillasolis/Documents/GitHub/complete-anvil/anvil_backend/env/lib/python3.12/site-packages/sqlalchemy/ext/asyncio/session.py", line 1030, in close
    |     await greenlet_spawn(self.sync_session.close)
    |           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    |   File "/Users/jhordanandresasprillasolis/Documents/GitHub/complete-anvil/anvil_backend/env/lib/python3.12/site-packages/sqlalchemy/util/concurrency.py", line 99, in greenlet_spawn
    |     _not_implemented()
    |   File "/Users/jhordanandresasprillasolis/Documents/GitHub/complete-anvil/anvil_backend/env/lib/python3.12/site-packages/sqlalchemy/util/concurrency.py", line 79, in _not_implemented
    |     raise ValueError(
    | ValueError: the greenlet library is required to use this function. No module named 'greenlet'
    +---------------- 2 ----------------
    | Traceback (most recent call last):
    |   File "/Users/jhordanandresasprillasolis/Documents/GitHub/complete-anvil/anvil_backend/env/lib/python3.12/site-packages/dishka/async_container.py", line 222, in close
    |     await exit_generator.callable.asend(exception)  # type: ignore[attr-defined]
    |     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    |   File "/Users/jhordanandresasprillasolis/Documents/GitHub/complete-anvil/anvil_backend/src/app/infrastructure/persistence_sqla/provider.py", line 58, in get_main_async_session
    |     async with async_session_factory() as session:
    |                ^^^^^^^^^^^^^^^^^^^^^^^
    |   File "/Users/jhordanandresasprillasolis/Documents/GitHub/complete-anvil/anvil_backend/env/lib/python3.12/site-packages/sqlalchemy/ext/asyncio/session.py", line 1085, in __aexit__
    |     await asyncio.shield(task)
    |   File "/Users/jhordanandresasprillasolis/Documents/GitHub/complete-anvil/anvil_backend/env/lib/python3.12/site-packages/sqlalchemy/ext/asyncio/session.py", line 1030, in close
    |     await greenlet_spawn(self.sync_session.close)
    |           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    |   File "/Users/jhordanandresasprillasolis/Documents/GitHub/complete-anvil/anvil_backend/env/lib/python3.12/site-packages/sqlalchemy/util/concurrency.py", line 99, in greenlet_spawn
    |     _not_implemented()
    |   File "/Users/jhordanandresasprillasolis/Documents/GitHub/complete-anvil/anvil_backend/env/lib/python3.12/site-packages/sqlalchemy/util/concurrency.py", line 79, in _not_implemented
    |     raise ValueError(
    | ValueError: the greenlet library is required to use this function. No module named 'greenlet'
    +---------------------------------
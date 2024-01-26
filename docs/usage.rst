Usage
=====

Here's an example of how to query a server using the Source protocol:

.. code-block:: python

    import asyncio
    from opengsq.protocols import Source

    async def main():
        source = Source(host='45.147.5.5', port=27015)
        info = await source.get_info()
        print(info)

    asyncio.run(main())

You can also use the Source Remote Console:

.. code-block:: python

    import asyncio
    from opengsq.exceptions import AuthenticationException
    from opengsq.protocols import Source

    async def main():
        with Source.RemoteConsole('123.123.123.123', 27015) as rcon:
            try:
                await rcon.authenticate('serverRconPassword')
                result = await rcon.send_command('cvarlist')
                print(result)
            except AuthenticationException:
                print('Failed to authenticate')

    asyncio.run(main())

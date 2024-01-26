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
    from opengsq.rcon_protocols.source_rcon import SourceRcon

    async def main():
        with SourceRcon("123.123.123.123", 27015) as source_rcon:
            try:
                await source_rcon.authenticate("serverRconPassword")
            except AuthenticationException:
                print('Failed to authenticate')

            response = await source_rcon.send_command("cvarlist")
            print(response)

    asyncio.run(main())

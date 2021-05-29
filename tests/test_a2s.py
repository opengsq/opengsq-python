from opengsq.protocols import A2S

server = A2S(address='', query_port=27015, timeout=5.0, engine=A2S.SOURCE)

def test_query():
    print('\n1. query()')
    print(server.query().to_json(indent=4))

def test_get_info():
    print('\n2. get_info()')
    print(server.get_info())

def test_get_players():
    print('\n3. get_players()')
    print(server.get_players())

def test_get_rules():
    print('\n4. get_rules()')
    print(server.get_rules())

from opengsq import Mordhau

server = Mordhau(address='', query_port=27015)

def test_query():
    print('\n1. query()')
    print(server.query().to_json(indent=4))

def test_get_info():
    print('\n2. get_info()')
    print(server.get_info())

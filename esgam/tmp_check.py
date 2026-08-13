from app import app

with app.test_client() as c:
    resp = c.get('/')
    print(resp.status_code)
    print(resp.data[:400].decode('utf-8', 'ignore'))

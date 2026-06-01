import os
import requests
import urllib3
from requests.adapters import HTTPAdapter
from dotenv import load_dotenv

class CustomSSLAdapter(HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        ctx = urllib3.util.ssl_.create_urllib3_context()
        ctx.options |= 0x4  
        kwargs['ssl_context'] = ctx
        return super(CustomSSLAdapter, self).init_poolmanager(*args, **kwargs)

load_dotenv("backend/.env")

TOKEN = os.getenv("KDCA_CONTENT_TOKEN").replace('&cntntsSn', '').strip()
base_url = "https://api.kdca.go.kr/api/provide/healthInfo"
session = requests.Session()
session.mount('https://', CustomSSLAdapter())

res = session.get(base_url, params={'TOKEN': TOKEN, 'cntntsSn': '6680'}, timeout=5)
with open('backend/eda/test_out.xml', 'w', encoding='utf-8') as f:
    f.write(res.text)
print("Saved to backend/eda/test_out.xml")

"""Isolated database and disabled provider for repeatable browser tests."""
import os
from pathlib import Path
import sys
import tempfile
import uvicorn

sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
with tempfile.TemporaryDirectory(prefix='signal-desk-e2e-') as tmp:
    os.environ['MARKET_DB_PATH']=str(Path(tmp)/'market.db')
    os.environ['MARKET_FEED_DISABLED']='1'
    uvicorn.run('backend.main:app',host='127.0.0.1',port=8005)

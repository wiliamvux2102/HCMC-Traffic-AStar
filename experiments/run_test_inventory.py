"""Execute the repository's tests and diagnostics and retain sanitized logs."""
from pathlib import Path
import json
import os
import re
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
OUT=Path(os.environ.get('ROUTING_AUDIT_OUTPUT', str(ROOT/'experiments/results/audit-2026-10-11')))
OUT.mkdir(parents=True,exist_ok=True)
env=dict(os.environ)
env['PYTHONPATH']=os.pathsep.join(filter(None, [str(ROOT), env.get('PYTHONPATH', '')]))
env['PYTHONDONTWRITEBYTECODE']='1'
env['PYTEST_DISABLE_PLUGIN_AUTOLOAD']='1'
jobs=[('pytest_tests',['-m','pytest','tests','-v','--tb=short','-p','no:cacheprovider'])]
jobs += [(p.stem,['-m','src.scripts.'+p.stem]) for p in sorted((ROOT/'src/scripts').glob('test*.py'))]
jobs += [('cli_help',['main.py','--help'])]
results=[]
for name,args in jobs:
    started=time.perf_counter()
    try:
        r=subprocess.run([sys.executable,'-B','-X','utf8',*args],cwd=ROOT,env=env,
                         stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding='utf-8',errors='replace',timeout=180)
        output=r.stdout; status='passed' if r.returncode==0 else 'failed'; code=r.returncode
    except subprocess.TimeoutExpired as e:
        output=e.stdout or b''
        if isinstance(output,bytes): output=output.decode('utf-8','replace')
        status='timeout';code=None
    output=re.sub(r'(?i)(apiKey|api_key|access_token|token)(=|%3D)[^&\s\"\']+',r'\1\2[REDACTED]',output)
    (OUT/(name+'.log')).write_text(output,encoding='utf-8')
    errors=[x for x in output.splitlines() if any(t in x for t in ['Error:','FAILED','passed','failed','PASSED','not found'])]
    result={'name':name,'status':status,'exit_code':code,'elapsed_s':time.perf_counter()-started,'summary':errors[-8:]}
    results.append(result)
    (OUT/'test-inventory.json').write_text(json.dumps(results,indent=2,ensure_ascii=False),encoding='utf-8')
    print(name,status, str(errors[-2:]),flush=True)
print('INVENTORY COMPLETE',flush=True)

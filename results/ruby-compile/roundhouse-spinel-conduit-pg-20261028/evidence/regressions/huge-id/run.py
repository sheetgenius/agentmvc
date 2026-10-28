import json,subprocess
from pathlib import Path
rows=[]
for source in sorted(Path('/probes').glob('*.rb')):
 row={'source':source.name}
 for kind,cmd in [('ruby',['ruby',str(source)]),('compile',['spinel','--cc=clang',str(source),'-o','/tmp/repro'])]:
  r=subprocess.run(cmd,capture_output=True,text=True,timeout=120)
  row[kind]={'exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr}
 if row['compile']['exit']==0:
  r=subprocess.run(['/tmp/repro'],capture_output=True,text=True,timeout=10)
  row['native']={'exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr}
 rows.append(row)
 print(json.dumps(row),flush=True)
Path('/probes/'+__import__('sys').argv[1]+'.json').write_text(json.dumps(rows,indent=2)+'\n')

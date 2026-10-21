import json,subprocess
from pathlib import Path
rows=[]
for source in sorted(Path('.').glob('*.rb')):
 row={'source':str(source)}
 for label,args in [('cruby',['ruby',str(source)]),('types',['spinel','--emit-rbs',str(source),'-o','/tmp/types.rbs']),('compile',['spinel','--cc=clang',str(source),'-o','/tmp/probe'])]:
  r=subprocess.run(args,capture_output=True,text=True,timeout=90);row[label]={'exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr}
  if label=='types' and r.returncode==0: row['inferred']=Path('/tmp/types.rbs').read_text()
 if row['compile']['exit']==0:
  r=subprocess.run(['/tmp/probe'],capture_output=True,text=True,timeout=10);row['compiled']={'exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr};row['matches_cruby']=row['compiled']==row['cruby']
 rows.append(row);print(json.dumps(row),flush=True)
Path('results.json').write_text(json.dumps(rows,indent=2)+'\n')

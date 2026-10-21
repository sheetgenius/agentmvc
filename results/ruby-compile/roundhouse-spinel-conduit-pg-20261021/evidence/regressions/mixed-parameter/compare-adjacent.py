import json,subprocess
from pathlib import Path
rows=[]
for condition in ['parent','introduced']:
 p=Path(condition);source=p/'driver.rb';source.write_text('require "json"\nrequire_relative "app/models/probe"\nProbe.run\n');row={'condition':condition,'emitted_signature':(p/'app/models/probe.rbs').read_text()}
 for label,args in [('cruby',['ruby',str(source)]),('compile',['spinel','--rbs',str(p/'app/models'),'--cc=clang',str(source),'-o','/tmp/probe'])]:
  r=subprocess.run(args,capture_output=True,text=True,timeout=90);row[label]={'exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr}
 if row['compile']['exit']==0:
  r=subprocess.run(['/tmp/probe'],capture_output=True,text=True,timeout=10);row['compiled']={'exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr};row['matches_cruby']=row['compiled']==row['cruby']
 rows.append(row);print(json.dumps(row),flush=True)
Path('results-adjacent.json').write_text(json.dumps(rows,indent=2)+'\n')

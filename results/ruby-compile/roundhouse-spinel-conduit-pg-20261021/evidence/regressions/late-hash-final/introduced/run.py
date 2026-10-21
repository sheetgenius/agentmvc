import json,subprocess,time
from pathlib import Path
rows=[]
for source in sorted(Path('.').glob('*.rb')):
 row={'source':str(source)}
 for label,args in [('cruby',['ruby',str(source)]),('types',['/after/bin/spinel','--emit-rbs',str(source),'-o',str(source.with_suffix('.rbs'))]),('compile',['/after/bin/spinel','--cc=clang',str(source),'-o','/tmp/probe'])]:
  r=subprocess.run(args,capture_output=True,text=True,timeout=90); row[label]={'exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr}; Path(str(source)+'.'+label+'.stdout').write_text(r.stdout); Path(str(source)+'.'+label+'.stderr').write_text(r.stderr)
 if row['compile']['exit']==0:
  r=subprocess.run(['/tmp/probe'],capture_output=True,text=True,timeout=10); row['compiled']={'exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr}; row['matches_cruby']=row['compiled']==row['cruby']
 rows.append(row); print(json.dumps(row),flush=True)
Path('results.json').write_text(json.dumps(rows,indent=2)+'\n')

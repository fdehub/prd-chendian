"""Validate requirements-package structure without executing package code. Stdlib only."""
from pathlib import Path
import argparse, hashlib, json, re, sys

ROLES={'prd','api','dictionary','prototype','trace','fixtures','review','verification','readme'}

def validate(root):
    root=Path(root).resolve();errors=[];checked=[];artifacts={}
    def fail(message):errors.append(message)
    def safe_path(value):
        if not isinstance(value,str) or not value or Path(value).is_absolute() or re.match(r'^[A-Za-z]:',value):raise ValueError('path must be relative')
        if '..' in Path(value.replace('\\','/')).parts:raise ValueError('parent traversal is forbidden')
        path=(root/value).resolve()
        if not path.is_relative_to(root):raise ValueError('path escapes bundle')
        return path
    def load(path):return json.loads(path.read_text(encoding='utf-8-sig'))
    try:m=load(root/'requirements-manifest.json')
    except (OSError,ValueError) as e:return {'result':'FAIL','errors':['manifest: '+str(e)],'checked':[]}
    if not isinstance(m,dict):return {'result':'FAIL','errors':['manifest must be an object'],'checked':[]}
    if not isinstance(m.get('version'),str) or not m['version'].strip():fail('version required')
    if m.get('scope') not in ['full','partial']:fail('scope must be full/partial')
    if m.get('status') not in ['proposal','reviewed','approved']:fail('status must be proposal/reviewed/approved; document validation never grants approval')
    if m.get('scope')=='partial' and not m.get('omissions'):fail('partial scope must list omissions')
    entries=m.get('artifacts',[])
    if not isinstance(entries,list):fail('artifacts must be a list');entries=[]
    for a in entries:
        try:
            if not isinstance(a,dict) or a.get('role') not in ROLES:raise ValueError('unknown artifact role')
            p=safe_path(a.get('path'))
            if not p.is_file() or p.stat().st_size==0:raise ValueError('file missing or empty')
            if a.get('sha256') and hashlib.sha256(p.read_bytes()).hexdigest()!=a['sha256']:raise ValueError('sha256 mismatch')
            artifacts.setdefault(a['role'],[]).append(p);checked.append(a['role']+': '+a['path'])
            if p.suffix=='.json':load(p)
        except (OSError,ValueError) as e:fail(str(a.get('path') if isinstance(a,dict) else '?')+': '+str(e))
    if m.get('scope')=='full':
        for role in sorted(ROLES-artifacts.keys()):fail('missing role: '+role)
    trace='\n'.join(p.read_text(encoding='utf-8-sig') for p in artifacts.get('trace',[]))
    all_ids=set()
    for p in artifacts.get('api',[]):
        try:
            spec=load(p)
            if not str(spec.get('openapi','')).startswith('3.'):raise ValueError('OpenAPI 3 JSON required')
            def deref(value):
                if not value.startswith('#/'):raise ValueError('inline local $ref required in this validator; resolve external refs to a bundled JSON first')
                v=spec
                for key in value[2:].split('/'):v=v[key.replace('~1','/').replace('~0','~')]
                return v
            def walk(v):
                if isinstance(v,dict):
                    if '$ref' in v:deref(v['$ref'])
                    if v.get('type')=='object' and not set(v.get('required',[]))<=set(v.get('properties',{})):raise ValueError('required property has no definition')
                    for item in v.values():walk(item)
                elif isinstance(v,list):
                    for item in v:walk(item)
            walk(spec);ids=set()
            if not spec.get('paths'):raise ValueError('no API paths')
            for path,methods in spec['paths'].items():
                inherited=methods.get('parameters',[])
                for method,op in methods.items():
                    if method not in ['get','post','put','patch','delete','head','options','trace']:continue
                    oid=op.get('operationId')
                    if not isinstance(oid,str) or not oid:raise ValueError('operationId missing')
                    if oid in ids:raise ValueError('duplicate operationId: '+oid)
                    if oid in all_ids:raise ValueError('operationId duplicates another API file: '+oid)
                    ids.add(oid)
                    all_ids.add(oid)
                    if not op.get('responses'):raise ValueError('responses missing: '+oid)
                    ps=[deref(x['$ref']) if '$ref' in x else x for x in inherited+op.get('parameters',[])]
                    actual={x['name'] for x in ps if x.get('in')=='path' and x.get('required') is True}
                    if actual!=set(re.findall(r'\{([^}]+)\}',path)):raise ValueError('path parameter mismatch: '+oid)
                    if trace and oid not in trace:raise ValueError('operation missing from trace: '+oid)
            checked.append('OpenAPI references/IDs/paths/trace: '+str(len(ids)))
        except (OSError,ValueError,KeyError,TypeError) as e:fail(p.name+': '+str(e))
    reqs=m.get('requirements',[]);cases=m.get('acceptanceCases',[])
    if not isinstance(reqs,list):fail('requirements must be a list');reqs=[]
    if not isinstance(cases,list):fail('acceptanceCases must be a list');cases=[]
    if m.get('scope')=='full' and (not reqs or not cases):fail('full package requires structured requirements and acceptanceCases')
    req_ids=[r.get('id') if isinstance(r.get('id'),str) and r['id'] else None for r in reqs if isinstance(r,dict)]
    case_ids=[c.get('id') if isinstance(c.get('id'),str) and c['id'] else None for c in cases if isinstance(c,dict)]
    if len(req_ids)!=len(reqs) or None in req_ids or len(req_ids)!=len(set(req_ids)):fail('invalid/duplicate requirement IDs')
    if len(case_ids)!=len(cases) or None in case_ids or len(case_ids)!=len(set(case_ids)):fail('invalid/duplicate acceptance IDs')
    linked=set()
    for r in reqs:
        if not isinstance(r,dict):continue
        rid=str(r.get('id'))
        if r.get('phase') not in ['P0','P1','excluded']:fail(rid+': phase must be P0/P1/excluded')
        if r.get('phase')!='P0':continue
        if not isinstance(r.get('pageIds'),list) or not r['pageIds'] or not all(isinstance(x,str) and x for x in r['pageIds']):fail(rid+': pageIds required')
        ops=r.get('operationIds',[])
        if not isinstance(ops,list) or not all(isinstance(x,str) for x in ops):fail(rid+': operationIds must be a string list');ops=[]
        if not ops and not (r.get('localOnly') is True and r.get('localReason')):fail(rid+': real operationIds or explicit localOnly/localReason required')
        if set(ops)-all_ids:fail(rid+': unknown operationId')
        linked.update(ops)
        ac=r.get('acceptanceIds',[])
        if not isinstance(ac,list) or not all(isinstance(x,str) for x in ac):fail(rid+': acceptanceIds must be a string list');ac=[]
        if not ac or set(ac)-set(case_ids):fail(rid+': missing/unknown acceptanceIds')
        for cid in ac:
            found=next((c for c in cases if isinstance(c,dict) and c.get('id')==cid),{})
            if rid not in found.get('requirementIds',[]):fail(rid+': acceptance reverse reference missing: '+str(cid))
    for c in cases:
        if not isinstance(c,dict):continue
        cid=str(c.get('id'))
        cr=c.get('requirementIds',[])
        if not isinstance(cr,list) or not all(isinstance(x,str) for x in cr):fail(cid+': requirementIds must be a string list');cr=[]
        if not cr or set(cr)-set(req_ids):fail(cid+': unknown/missing requirementIds')
        for key in ['given','when','then']:
            if not isinstance(c.get(key),dict) or not c[key]:fail(cid+': nonempty structured '+key+' required')
        if c.get('then') in [{'result':'正确'},{'result':'正常'},{'result':'成功'},{'result':'correct'}]:fail(cid+': then must state objective values, not a vague label')
    if m.get('scope')=='full' and all_ids-linked:fail('API operations unlinked to requirements: '+', '.join(sorted(all_ids-linked)))
    checked.append('structured requirement/case links: '+str(len(reqs))+'/'+str(len(cases)))
    return {'result':'FAIL' if errors else 'PASS','errors':errors,'checked':checked,'scope':'Structure, JSON, references and trace only. Not full OpenAPI conformance, business correctness, user approval or software acceptance.'}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('bundle');ap.add_argument('--report');args=ap.parse_args()
    report=validate(args.bundle);output=json.dumps(report,ensure_ascii=False,indent=2)
    if args.report:Path(args.report).write_text(output,encoding='utf-8')
    print(output)
    return 0 if report['result']=='PASS' else 1
if __name__=='__main__':sys.exit(main())

import {readFileSync,readdirSync,lstatSync,realpathSync} from 'node:fs';
import {resolve,join,relative,sep} from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash,createPublicKey,verify} from 'node:crypto';

const args=process.argv.slice(2);let root=fileURLToPath(new URL('../',import.meta.url));let trusted;
for(let i=0;i<args.length;i++){
  if(args[i]==='--trusted-fingerprint')trusted=args[++i];
  else if(args[i]==='--root')root=args[++i];
  else throw new Error('Unknown argument: '+args[i]);
}
function canonical(v){
  if(Array.isArray(v))return '['+v.map(canonical).join(',')+']';
  if(v&&typeof v==='object')return '{'+Object.keys(v).sort().map(k=>JSON.stringify(k)+':'+canonical(v[k])).join(',')+'}';
  return JSON.stringify(v);
}
function digest(b){return createHash('sha256').update(b).digest('hex');}
try{
  root=realpathSync(resolve(root));
  const p=JSON.parse(readFileSync(join(root,'PROVENANCE.json'),'utf8'));
  if(p.format!=='prd-skill-release-v1')throw new Error('Unsupported provenance format');
  const payload=Buffer.from(p.signedPayloadBase64,'base64');
  if(!payload.equals(Buffer.from(canonical(p.release),'utf8')))throw new Error('Release metadata differs from signed payload');
  const spki=Buffer.from(p.release.publicKeySpkiBase64,'base64');
  const fingerprint=digest(spki);
  if(fingerprint!==p.release.keyFingerprintSha256)throw new Error('Public-key fingerprint mismatch');
  const key=createPublicKey({key:spki,format:'der',type:'spki'});
  if(key.asymmetricKeyType!=='ec'||key.asymmetricKeyDetails?.namedCurve!=='prime256v1')throw new Error('Expected P-256 public key');
  if(!verify('sha256',payload,{key,dsaEncoding:'der'},Buffer.from(p.signatureBase64,'base64')))throw new Error('Signature invalid');
  const expected=new Set();
  for(const item of p.release.files){
    const name=item.path;
    if(typeof name!=='string'||name.includes('\\')||name.startsWith('/')||name.includes(':')||name.split('/').some(x=>x==='..'||!x)||name==='PROVENANCE.json'||expected.has(name))throw new Error('Unsafe/duplicate signed path');
    const file=realpathSync(resolve(root,name));const rel=relative(root,file);
    if(rel.startsWith('..'+sep)||rel==='..'||resolve(root,rel)!==file)throw new Error('Signed path escapes root');
    const data=readFileSync(file);
    if(data.length!==item.bytes||digest(data)!==item.sha256)throw new Error('File changed: '+name);
    expected.add(name);
  }
  const actual=[];
  function walk(dir){for(const n of readdirSync(dir)){if(dir===root&&n==='.git')continue;const path=join(dir,n);const stat=lstatSync(path);if(stat.isSymbolicLink())throw new Error('Symlinks not permitted');if(stat.isDirectory())walk(path);else if(stat.isFile())actual.push(relative(root,path).split(sep).join('/'));}}
  walk(root);
  if(actual.filter(x=>x!=='PROVENANCE.json').length!==expected.size||actual.some(x=>x!=='PROVENANCE.json'&&!expected.has(x)))throw new Error('Unsigned additional files detected');
  if(!trusted){
    console.log(JSON.stringify({status:'UNPINNED',integrity:'PASS',author:p.release.author,skillId:p.release.skillId,keyFingerprint:fingerprint,message:'Files and signature match the included key; author identity is NOT established. Obtain the fingerprint from a trusted author channel, not this package.'},null,2));
    process.exitCode=2;
  }else{
    if(!/^[a-f0-9]{64}$/i.test(trusted)||trusted.toLowerCase()!==fingerprint)throw new Error('Trusted fingerprint does not match signer');
    console.log(JSON.stringify({status:'PASS',author:p.release.author,skillId:p.release.skillId,version:p.release.version,files:expected.size,keyFingerprint:fingerprint,scope:'Matches the independently supplied public-key fingerprint and signed file list; not proof of real-world identity or prevention of copying.'},null,2));
  }
}catch(e){console.error(JSON.stringify({status:'FAIL',message:e.message}));process.exitCode=1;}

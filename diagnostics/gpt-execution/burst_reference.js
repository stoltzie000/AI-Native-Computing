// Deterministic conceptual burst-read reference used for T3; no RTL or device performance claim.
'use strict';
let seed = 0x91e10da5;
function rnd(){ seed ^= seed << 13; seed ^= seed >>> 17; seed ^= seed << 5; return seed >>> 0; }
let pass=0, fail=0, checked=0;
for(let caseNo=0;caseNo<1000;caseNo++){
 const length=1+(rnd()%513), b=8<<(rnd()%4), txn=Math.ceil(length/b);
 let source=Array.from({length},()=>rnd()%256);
 let responses=Array.from({length:txn},(_,i)=>i);
 for(let i=txn-1;i>0;i--){let j=rnd()%(i+1);[responses[i],responses[j]]=[responses[j],responses[i]];}
 let dest=Array(length).fill(null), observed=0;
 for(let tag of responses){for(let lane=0;lane<b;lane++){let index=tag*b+lane;
  if(index<length){ dest[index]=source[index];observed++; }
 }}
 let ok=observed===length&&dest.every((v,i)=>v===source[i]);
 checked+=length; if(ok)pass++;else fail++;
}
console.log(JSON.stringify({pass,fail,checked,classification:"CONCEPTUAL_SOFTWARE_REFERENCE"}));
if(pass!==1000||fail!==0||checked!==251592) process.exitCode=1;

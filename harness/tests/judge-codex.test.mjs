import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, writeFileSync, readFileSync, rmSync, existsSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, resolve } from 'node:path';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { cleanEnv, validVerdict, runCodex } from '../judge-codex.mjs';
import { JUDGE_SYSTEM, VERDICT_SCHEMA, judgePrompt, blind } from '../../scorers/vendor/eval-lib/judge-core.mjs';

const verdict = { scores_A: { correctness: 5, completeness: 4, usefulness: 3 }, scores_B: { correctness: 2, completeness: 2, usefulness: 2 }, winner: 'A', rationale: 'Synthetic test.' };
const temp = mkdtempSync(join(tmpdir(), 'judge-codex-test-'));
const oldPath = process.env.PATH;
const adapter = resolve(fileURLToPath(new URL('../judge-codex.mjs', import.meta.url)));
function fake(body) {
  writeFileSync(join(temp, 'codex'), `#!${process.execPath}\n${body}`, { mode: 0o755 });
  process.env.PATH = `${temp}:${oldPath}`;
}
function emit(value) { return `console.log(${JSON.stringify(JSON.stringify(value))});`; }
function final(v = verdict) { return emit({ type: 'item.completed', item: { type: 'agent_message', text: JSON.stringify(v) } }); }
const opts = { prompt: 'Synthetic question', systemPrompt: JUDGE_SYSTEM, model: 'test-model', jsonSchema: VERDICT_SCHEMA, timeoutMs: 2000 };

test('login-only environment and strict schema validation', () => {
  process.env.OPENAI_API_KEY = 'synthetic-key';
  process.env.CODEX_API_KEY = 'synthetic-key';
  process.env.OPENAI_BASE_URL = 'https://invalid.example';
  assert.equal(cleanEnv().OPENAI_API_KEY, undefined);
  assert.equal(cleanEnv().CODEX_API_KEY, undefined);
  assert.equal(cleanEnv().OPENAI_BASE_URL, undefined);
  delete process.env.OPENAI_API_KEY; delete process.env.CODEX_API_KEY; delete process.env.OPENAI_BASE_URL;
  assert.ok(validVerdict(verdict));
  assert.ok(!validVerdict({ ...verdict, unexpected: true }));
  assert.ok(!validVerdict({ ...verdict, scores_A: { ...verdict.scores_A, correctness: 0 } }));
  assert.ok(!validVerdict({ ...verdict, winner: 'ref' }));
});

test('CLI isolation, unchanged schema/system, stdin prompt and structured verdict', async () => {
  fake(`const fs=require('node:fs'); const a=process.argv.slice(2);
const assert=require('node:assert/strict');
assert.ok(a.includes('--ephemeral') && a.includes('--ignore-user-config') && a.includes('--ignore-rules'));
assert.equal(a[a.indexOf('--sandbox')+1],'read-only');
for(const c of ['features.shell_tool=false','features.apps=false','features.multi_agent=false','web_search="disabled"','forced_login_method="chatgpt"','model_reasoning_effort="high"']) assert.ok(a.includes(c));
const c=a.find(x=>x.startsWith('model_instructions_file='));
assert.equal(fs.readFileSync(JSON.parse(c.slice(c.indexOf('=')+1)),'utf8'),${JSON.stringify(JUDGE_SYSTEM)});
assert.deepEqual(JSON.parse(fs.readFileSync(a[a.indexOf('--output-schema')+1])),${JSON.stringify(VERDICT_SCHEMA)});
assert.equal(fs.readFileSync(0,'utf8'),'Synthetic question');
${final()}`);
  const calls = []; const r = await runCodex({ ...opts, onCall: (c) => calls.push(c) });
  assert.ok(r.ok); assert.deepEqual(r.json.structured_output, verdict); assert.equal(r.toolCalls, 0);
  assert.equal(calls.length, 1); assert.ok(calls[0].wallMs > 0);
});

test('successful metadata and rationale containing 429 are not rate limits', async () => {
  fake(emit({type:'thread.started',thread_id:'synthetic-429-thread'}) +
    final({...verdict,rationale:'Synthetic date 1429 and usage limit discussion.'}) +
    emit({type:'turn.completed',usage:{input_tokens:429,output_tokens:42}}));
  const r=await runCodex(opts);
  assert.ok(r.ok); assert.equal(r.rateLimited,false);
});

test('invalid verdict retries exactly once; rate limits and tool use fail closed', async () => {
  fake(emit({ type: 'item.completed', item: { type: 'agent_message', text: 'not JSON' } }));
  const calls = []; const r = await runCodex({ ...opts, onCall: c => calls.push(c) });
  assert.ok(!r.ok); assert.equal(calls.length, 2);
  fake(emit({ type: 'turn.failed', error: { message: 'usage limit reached' } }) + 'process.exitCode=1;');
  const limited = []; assert.ok((await runCodex({ ...opts, onCall: c => limited.push(c) })).rateLimited);
  assert.equal(limited.length, 1);
  fake(emit({ type: 'item.completed', item: { type: 'command_execution', command: 'synthetic' } }) + final());
  assert.equal((await runCodex(opts)).error, 'unexpected tool use');
});

test('both orders, limits, resume, unchanged prompt assembly, and stale provenance rejection', () => {
  const bench=join(temp,'bench.json'), traces=join(temp,'traces.jsonl'), refs=join(temp,'refs.jsonl'), out=join(temp,'judgments.jsonl');
  writeFileSync(bench,JSON.stringify({questions:'questions.jsonl',refs:'refs.jsonl'}));
  writeFileSync(join(temp,'questions.jsonl'),JSON.stringify({id:'synthetic-1',question:'2 + 2?',rubric:['Addition'],category:'test'})+'\n');
  writeFileSync(traces,JSON.stringify({itemId:'synthetic-1',answer:{text:'**4**'},runId:'synthetic',engine:{arm:'test',commit:'abc'}})+'\n');
  writeFileSync(refs,JSON.stringify({id:'synthetic-1',ok:true,answer:'4'})+'\n');
  const promptLog=join(temp,'prompts.jsonl');
  fake(`if(process.argv.includes('--version')) { console.log('codex-test'); process.exit(0); }
const fs=require('node:fs');fs.appendFileSync(${JSON.stringify(promptLog)},JSON.stringify(fs.readFileSync(0,'utf8'))+'\\n');${final()}`);
  const args=[adapter,'--bench',temp,'--traces',traces,'--out',out,'--gap-ms','0','--strict','--judge-model','test-model'];
  let r=spawnSync(process.execPath,[...args,'--dry-run'],{encoding:'utf8'});assert.equal(r.status,0);assert.ok(!existsSync(out));
  r=spawnSync(process.execPath,[...args,'--limit','1'],{encoding:'utf8'});assert.equal(r.status,0,r.stderr);
  assert.equal(readFileSync(out,'utf8').trim().split('\n').length,1);
  r=spawnSync(process.execPath,args,{encoding:'utf8'});assert.equal(r.status,0,r.stderr);
  const rows=readFileSync(out,'utf8').trim().split('\n').map(JSON.parse);
  assert.deepEqual(rows.map(x=>x.order).sort(),['boarA','boarB']);
  assert.ok(rows.every(x=>x.judgeVersion==='judge.v1-codex' && x.sampling.reasoningEffort==='high' && x.cliVersion==='codex-test'));
  assert.equal(readFileSync(promptLog,'utf8').trim().split('\n').length,2);
  const prompts=readFileSync(promptLog,'utf8').trim().split('\n').map(JSON.parse);
  assert.ok(prompts.every(p=>p===judgePrompt({question:'2 + 2?',notes:'Addition',answerA:blind('**4**'),answerB:blind('4')})));
  r=spawnSync(process.execPath,args,{encoding:'utf8'});assert.equal(r.status,0);
  assert.equal(readFileSync(promptLog,'utf8').trim().split('\n').length,2);
  writeFileSync(traces,readFileSync(traces,'utf8')+'\n');
  r=spawnSync(process.execPath,args,{encoding:'utf8'});assert.equal(r.status,7);
  assert.equal(readFileSync(promptLog,'utf8').trim().split('\n').length,2);
  const parallelOut=join(temp,'parallel.jsonl');
  r=spawnSync(process.execPath,[...args.slice(0,args.indexOf('--out')), '--out',parallelOut,'--gap-ms','0','--judge-model','test-model','--concurrency','4'],{encoding:'utf8'});
  assert.equal(r.status,0,r.stderr);
  const parallelRows=readFileSync(parallelOut,'utf8').trim().split('\n').map(JSON.parse);
  assert.equal(parallelRows.length,2);
  assert.equal(new Set(parallelRows.map(x=>`${x.queryId}|${x.order}`)).size,2);
});

test.after(() => { process.env.PATH=oldPath; rmSync(temp,{recursive:true,force:true}); });

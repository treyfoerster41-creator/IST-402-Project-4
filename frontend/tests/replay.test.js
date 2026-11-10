import {test} from 'node:test';
import assert from 'node:assert/strict';
import {buildReplayBars} from '../src/replay.js';
const rows=[
{seq:1,identity:'late',source_ms:120000,price:12,day_volume:120},
{seq:2,identity:'late',source_ms:120000,price:13,day_volume:125},
{seq:3,identity:'early',source_ms:60000,price:10,day_volume:100}];
test('receipt prefix never applies a future revision',()=>{
assert.equal(buildReplayBars(rows,1)[0].close,12);
assert.equal(buildReplayBars(rows,2)[0].close,13);
});
test('out-of-order samples match backend reference OHLC/volume',()=>{
assert.deepEqual(buildReplayBars(rows,3),[
{time:60,open:10,high:10,low:10,close:10,volume:0,volume_known:false,complete:false},
{time:120,open:13,high:13,low:13,close:13,volume:25,volume_known:true,complete:false}]);
});
test('empty window is empty',()=>assert.deepEqual(buildReplayBars([],0),[]));

test('replay completion uses its receipt clock, not today',()=>{
const sample=[{seq:1,identity:'sample',source_ms:60000,received_ms:90000,price:10,day_volume:null}];
assert.equal(buildReplayBars(sample,1)[0].complete,false);
sample.push({seq:2,identity:'later',source_ms:120000,received_ms:120001,price:11,day_volume:null});
assert.equal(buildReplayBars(sample,2)[0].complete,true);
});

test('crypto volume remains explicitly unknown',()=>{
const crypto=rows.map(row=>({...row,symbol:'BTC-USD'}));
assert.ok(buildReplayBars(crypto,3).every(bar=>!bar.volume_known));
});

import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {indicators} from '../src/indicators.js';
const fixture=JSON.parse(readFileSync(new URL('../../backend/tests/fixtures/sma-reference.json',import.meta.url)));
const bars=fixture.prices.map((close,i)=>({time:(i+1)*60,close,complete:true}));
test('displayed SMA values and crosses match the pandas reference fixture',()=>{
  assert.deepEqual(indicators(bars,fixture.fast,fixture.slow),fixture.expected);
});
test('unfinished candle never changes averages or creates a signal',()=>{
  assert.deepEqual(indicators([...bars,{time:9999,close:999999,complete:false}],2,3),fixture.expected);
});
test('invalid windows and empty input return no indicators',()=>{
  assert.deepEqual(indicators(bars,8,3),[]);
  assert.deepEqual(indicators([],3,8),[]);
});

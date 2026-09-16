// Exercise the production renderer without requiring a browser or modifying exports.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const { test } = require('node:test');
const source = fs.readFileSync(path.join(__dirname, '..', 'index.js'), 'utf8');
const context = vm.createContext({});
vm.runInContext(source.slice(source.indexOf('function escapeChartText'), source.indexOf('function wireChart')), context);
const chart = context.buildChart;

test('missing observations break lines and never produce NaN or Infinity', () => {
  const svg = chart([{ label: 'a', value: 20 }, { label: 'b', value: null }, { label: 'c', value: 40 }]);
  const line = svg.match(/class="chart-line" d="([^"]*)"/)[1];
  assert.equal((line.match(/M/g) || []).length, 2);
  assert.equal((line.match(/L/g) || []).length, 0);
  assert.doesNotMatch(svg, /NaN|Infinity/);
});

test('zero, single point and missing series are handled', () => {
  for (const data of [[], [{ label: 'a', value: null }], [{ label: 'a', value: 0 }], [{ label: 'a', value: 0 }, { label: 'b', value: 0 }]]) {
    assert.doesNotMatch(chart(data), /NaN|Infinity/);
  }
  assert.match(chart([]), /데이터가 없습니다/);
});

test('fixed 0–100 axis, sparse dates and escaped labels', () => {
  const data = Array.from({ length: 90 }, (_, i) => ({ label: `day-${i}`, value: 50 }));
  data[0].label = '<script>alert(1)</script>';
  const svg = chart(data);
  assert.match(svg, />100<\/text>/);
  assert.equal((svg.match(/y="154"/g) || []).length, 3);
  assert.match(svg, /M 30.0 77.0/);
  assert.doesNotMatch(svg, /<script>/);
  assert.match(svg, /&lt;script&gt;/);
  assert.doesNotMatch(svg, /chart-value/);
});

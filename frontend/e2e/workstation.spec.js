import { test, expect } from '@playwright/test';

test('practice backtest displays indicators, accounting, trades and persists after refresh', async ({ page }) => {
  const errors=[]; page.on('pageerror', error=>errors.push(error.message));
  await page.goto('/');
  await expect(page.getByRole('heading', { name: 'Put the crossover to the test.' })).toBeVisible();
  await expect(page.getByTestId('indicator-summary')).toContainText('warming up');
  await page.getByLabel('Backtest data').selectOption('practice');
  await page.getByRole('button', { name: 'Run backtest', exact: true }).click();
  await expect(page.getByTestId('run-context')).toContainText('SYNTHETIC PRACTICE');
  await expect(page.getByTestId('run-context')).toContainText('47 closed candles');
  await expect(page.getByRole('table', { name: 'Orders and fills' })).toContainText('filled');
  await expect(page.getByRole('table', { name: 'Orders and fills' })).toContainText('BUY');
  await expect(page.getByRole('table', { name: 'Orders and fills' })).toContainText('SELL');
  const selected = await page.getByLabel('Saved runs').inputValue();
  const data=await (await page.request.get(`/api/trading/runs/${selected}`)).json();
  expect(data.points.some(p=>p.fast!=null && p.slow!=null)).toBeTruthy();
  expect(data.points.filter(p=>p.crossover).length).toBeGreaterThan(2);
  expect(Number(data.totals.equity)).toBeCloseTo(Number(data.totals.cash)+Number(data.totals.position_value),2);
  expect(Number(data.totals.total_pnl)).toBeCloseTo(Number(data.totals.realized)+Number(data.totals.unrealized),2);
  const metrics=await page.getByTestId('account-metrics').innerText();
  await page.reload();
  await expect(page.getByLabel('Saved runs')).toHaveValue(selected);
  await expect(page.getByTestId('account-metrics')).toHaveText(metrics, {useInnerText:true});
  await page.getByText('Recent signals and execution assumptions').click();
  await expect(page.getByText(/Decisions use closed bars as first known/)).toBeVisible();
  expect(errors).toEqual([]);
});

test('invalid SMA, empty Yahoo history, and provider outage stay understandable', async ({ page }) => {
  await page.goto('/');
  await page.getByLabel('Fast SMA', {exact:true}).fill('9');
  await expect(page.getByRole('button',{name:'Run backtest',exact:true})).toBeDisabled();
  await expect(page.getByText(/Use whole SMA lengths/)).toBeVisible();
  await page.getByLabel('Fast SMA',{exact:true}).fill('3');
  await page.getByLabel('Backtest data').selectOption('yahoo');
  await page.getByRole('button',{name:'Run backtest',exact:true}).click();
  await expect(page.getByRole('alert')).toContainText('No saved Yahoo observations');
  await page.getByRole('button',{name:'Simulate feed outage'}).click();
  await expect(page.locator('.status')).toContainText('unavailable');
  await page.getByRole('button',{name:'Recorded replay',exact:true}).click();
  await expect(page.getByText(/No saved observations for this instrument yet/)).toBeVisible();
  await page.getByLabel('Backtest data').selectOption('practice');
  await page.getByRole('button',{name:'Run backtest',exact:true}).click();
  await expect(page.getByTestId('run-context')).toContainText('completed');
});

test('paper account starts without fabricated trades, survives refresh, and stops', async ({page}) => {
  await page.goto('/');
  await page.getByRole('button',{name:'Start paper account'}).click();
  await expect(page.getByTestId('run-context')).toContainText('Paper account');
  await expect(page.getByText(/Warming up: 0 \/ 8/)).toBeVisible();
  await expect(page.getByRole('table',{name:'Orders and fills'})).toContainText('No orders yet');
  const id=await page.getByLabel('Saved runs').inputValue();
  await page.reload();
  await expect(page.getByLabel('Saved runs')).toHaveValue(id);
  await page.getByRole('button',{name:'Stop paper account'}).click();
  await expect(page.getByTestId('run-context')).toContainText('stopped');
  await expect(page.getByRole('button',{name:'Stop paper account'})).toHaveCount(0);
});

test('server rejects invalid settings without saving a run', async ({request}) => {
  const response=await request.post('/api/trading/runs',{data:{fast:10,slow:3}});
  expect(response.status()).toBe(422);
});

test('mobile layout keeps controls usable without page overflow', async ({page}) => {
  await page.setViewportSize({width:390,height:844});
  await page.goto('/');
  await page.getByLabel('Backtest data').selectOption('practice');
  await page.getByRole('button',{name:'Run backtest',exact:true}).click();
  await expect(page.getByTestId('account-metrics')).toBeVisible();
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth)).toBeTruthy();
});

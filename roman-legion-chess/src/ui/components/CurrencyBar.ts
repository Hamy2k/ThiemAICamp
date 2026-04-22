/**
 * Bottom currency bar — shows gold + gem amounts.
 * Phase 2: hardcoded 0. Phase 3+ will wire to gameStore.
 */

export interface CurrencyBarOptions {
  gold: number;
  gems: number;
}

export function createCurrencyBar(opts: CurrencyBarOptions): HTMLElement {
  const wrap = document.createElement('div');
  wrap.className =
    'flex items-center justify-center gap-6 px-4 py-2 rounded-full ' +
    'border border-gold/50 bg-obsidian/70 backdrop-blur-sm shadow-gold-soft';

  wrap.appendChild(makeCell('🪙', 'gold', opts.gold));
  const divider = document.createElement('div');
  divider.className = 'w-px h-5 bg-gold/40';
  wrap.appendChild(divider);
  wrap.appendChild(makeCell('💎', 'gem', opts.gems));

  return wrap;
}

function makeCell(icon: string, dataKey: string, amount: number): HTMLElement {
  const cell = document.createElement('div');
  cell.className = 'flex items-center gap-2';
  cell.dataset.currency = dataKey;

  const ic = document.createElement('span');
  ic.textContent = icon;
  ic.className = 'text-lg leading-none';
  cell.appendChild(ic);

  const amt = document.createElement('span');
  amt.className = 'font-numeric font-bold text-gold text-sm';
  amt.textContent = amount.toLocaleString();
  cell.appendChild(amt);

  return cell;
}

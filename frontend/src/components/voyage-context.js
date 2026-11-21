import {store} from '../stores/workspace.js';import {esc} from '../utils/format.js';import {cruiseStates} from '../constants/enums.js';import {badge} from './controls.js';
export const current=()=>store.data.cruises.find(c=>c.id===store.selected);
export const transects=()=>store.data.transects.filter(t=>t.cruise_id===store.selected&&t.status!=='cancelled');
export const transectOptions=()=>transects().map(t=>`<option value="${t.id}">${esc(t.code)} / ${Math.round(t.length_m)}m ${t.parent_id?'· 补航':''}</option>`).join('');
export const cruiseOptions=()=>store.data.cruises.map(c=>`<option value="${c.id}" ${c.id===store.selected?'selected':''}>${esc(c.code)} · ${cruiseStates[c.status]}</option>`).join('');
export const localTime=t=>new Date(t).toLocaleString('zh-CN',{timeZone:'Asia/Shanghai',hour12:false});
export function context(){const c=current();return `<section class="voyage-context"><div><small>CRUISE / 当前调查</small><h2>${esc(c.code)} <span>${esc(store.data.boats.find(b=>b.id===c.boat_id)?.name)}</span></h2></div><p>${localTime(c.depart)}<br>至 ${localTime(c.arrive)}</p><div>${badge(cruiseStates[c.status])}<small>${esc(c.purpose)}</small></div></section>`;}

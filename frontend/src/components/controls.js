import {esc} from '../utils/format.js';
export const field=(title,control)=>`<label>${title}${control}</label>`;
export const input=(name,type='text',value='',extra='')=>`<input name="${name}" type="${type}" value="${esc(value)}" required ${extra}>`;
export const select=(name,options)=>`<select name="${name}" required>${options}</select>`;
export const textarea=(name,value='')=>`<textarea name="${name}" rows="4" required>${esc(value)}</textarea>`;
export const badge=(text,kind='')=>`<span class="badge ${kind}">${esc(text)}</span>`;
export function table(headers,rows,empty='尚无记录，请按收件步骤办理。'){return `<div class="table-scroll"><table><thead><tr>${headers.map(h=>`<th>${esc(h)}</th>`).join('')}</tr></thead><tbody>${rows.length?rows.map(r=>`<tr>${r.map(v=>`<td>${v}</td>`).join('')}</tr>`).join(''):`<tr><td colspan="${headers.length}" class="empty">${esc(empty)}</td></tr>`}</tbody></table></div>`;}

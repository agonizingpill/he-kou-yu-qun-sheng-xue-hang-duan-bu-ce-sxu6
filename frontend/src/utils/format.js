export const esc=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
export const money=cents=>'¥'+(Number(cents||0)/100).toLocaleString('zh-CN',{minimumFractionDigits:2});
export const date=value=>new Date(value).toLocaleString('zh-CN',{hour12:false});

import {request} from '../api/client.js';import {reload} from '../stores/workspace.js';
export function bindForm(id,action,rerender){const form=document.getElementById(id);if(!form)return;form.onsubmit=async event=>{event.preventDefault();const button=form.querySelector('button');button.disabled=true;document.getElementById('notice').textContent='正在留存调查记录…';try{await action(Object.fromEntries(new FormData(form)));await reload();rerender('调查记录已更新');}catch(error){document.getElementById('notice').textContent=error.message;document.getElementById('notice').className='notice error';}finally{button.disabled=false;}};}
export function num(data,...keys){for(const key of keys)data[key]=Number(data[key]);return data;}
export {request};

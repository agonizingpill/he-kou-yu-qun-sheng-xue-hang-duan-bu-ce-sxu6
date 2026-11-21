import {request} from '../api/client.js';
export const store={data:{},selected:Number(localStorage.getItem('survey-cruise')||1),session:JSON.parse(localStorage.getItem('survey-session')||'null')};
export async function reload(){store.data=await request('/workspace');if(!store.data.cruises.some(c=>c.id===store.selected))store.selected=store.data.cruises[0]?.id;return store.data;}
export async function login(username,password){store.session=await request('/auth/login',{username,password});localStorage.setItem('survey-session',JSON.stringify(store.session));}
export function selectCruise(id){store.selected=+id;localStorage.setItem('survey-cruise',id);}
export function logout(){localStorage.removeItem('survey-session');location.reload();}

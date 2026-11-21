export async function request(path,body,method='POST'){
 const token=JSON.parse(localStorage.getItem('survey-session')||'null')?.token;
 const response=await fetch('/api'+path,{method:body===undefined?'GET':method,headers:{'Content-Type':'application/json',...(token?{Authorization:'Bearer '+token}:{})},...(body===undefined?{}:{body:JSON.stringify(body)})});
 const data=await response.json();if(!response.ok)throw new Error(typeof data.detail==='string'?data.detail:JSON.stringify(data.detail));return data;
}

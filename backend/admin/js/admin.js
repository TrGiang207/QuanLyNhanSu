const API='http://127.0.0.1:8000/api';
function user(){try{return JSON.parse(localStorage.getItem('user')||'null')}catch{return null}}
if(!user()||user().VaiTro!=='Admin'){location.href='../user/login.html'}
function logout(){localStorage.removeItem('user');location.href='../user/login.html'}
async function getJson(url,opt){const r=await fetch(url,opt);const j=await r.json();if(!r.ok)throw Error(j.detail||j.message||'Có lỗi');return j}

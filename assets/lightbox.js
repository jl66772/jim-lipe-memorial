(()=>{const links=[...document.querySelectorAll('.grid a')],lb=document.getElementById('lb'),img=lb.querySelector('img'),cnt=lb.querySelector('.count');let i=0;
function show(n){i=(n+links.length)%links.length;img.src=links[i].href;cnt.textContent=(i+1)+' / '+links.length;[i+1,i-1].forEach(k=>{const l=links[(k+links.length)%links.length];new Image().src=l.href})}
links.forEach((a,n)=>a.addEventListener('click',e=>{e.preventDefault();show(n);lb.classList.add('open')}));
const close=()=>{lb.classList.remove('open');img.src=''};
lb.querySelector('.prev').onclick=e=>{e.stopPropagation();show(i-1)};lb.querySelector('.next').onclick=e=>{e.stopPropagation();show(i+1)};lb.querySelector('.close').onclick=close;
lb.addEventListener('click',e=>{if(e.target===lb)close()});
document.addEventListener('keydown',e=>{if(!lb.classList.contains('open'))return;if(e.key==='ArrowRight')show(i+1);if(e.key==='ArrowLeft')show(i-1);if(e.key==='Escape')close()});
let x0=null;lb.addEventListener('touchstart',e=>x0=e.touches[0].clientX,{passive:true});lb.addEventListener('touchend',e=>{if(x0===null)return;const dx=e.changedTouches[0].clientX-x0;if(Math.abs(dx)>40)show(i+(dx<0?1:-1));x0=null});})();

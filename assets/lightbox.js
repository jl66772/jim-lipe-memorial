(()=>{const links=[...document.querySelectorAll('a.lb')],lb=document.getElementById('lb'),img=lb.querySelector('img'),cnt=lb.querySelector('.count');let list=links.map(a=>a.getAttribute('href')),i=0;
function show(n){i=(n+list.length)%list.length;img.src=list[i];cnt.textContent=(i+1)+' / '+list.length;[i+1,i-1].forEach(k=>{new Image().src=list[(k+list.length)%list.length]})}
window.openLB=href=>{const n=list.indexOf(href);show(n<0?0:n);lb.classList.add('open')};
links.forEach(a=>a.addEventListener('click',ev=>{ev.preventDefault();openLB(a.getAttribute('href'))}));
const close=()=>{lb.classList.remove('open');img.removeAttribute('src')};
lb.querySelector('.prev').onclick=ev=>{ev.stopPropagation();show(i-1)};lb.querySelector('.next').onclick=ev=>{ev.stopPropagation();show(i+1)};lb.querySelector('.close').onclick=close;
lb.addEventListener('click',ev=>{if(ev.target===lb)close()});
document.addEventListener('keydown',ev=>{if(!lb.classList.contains('open'))return;if(ev.key==='ArrowRight')show(i+1);if(ev.key==='ArrowLeft')show(i-1);if(ev.key==='Escape')close()});
let x0=null;lb.addEventListener('touchstart',ev=>x0=ev.touches[0].clientX,{passive:true});lb.addEventListener('touchend',ev=>{if(x0===null)return;const dx=ev.changedTouches[0].clientX-x0;if(Math.abs(dx)>40)show(i+(dx<0?1:-1));x0=null});})();

(()=>{const S=window.SITE,p=S.photos;if(!p.length)return;
// Photo of the Day: same photo all day (local date), changes daily
const d=new Date(),key=d.getFullYear()*10000+(d.getMonth()+1)*100+d.getDate();let h=key;h=Math.imul(h^(h>>>16),2246822507)>>>0;h=Math.imul(h^(h>>>13),3266489909)>>>0;
const s=p[h%p.length],a=document.getElementById('potd-link');if(a){document.getElementById('potd-img').src='media/full/'+s+'.webp';a.href='media/full/'+s+'.webp';a.onclick=ev=>{ev.preventDefault();openLB(a.getAttribute('href'))}}
// Birthday / remembrance notes
const md=String(d.getMonth()+1).padStart(2,'0')+'-'+String(d.getDate()).padStart(2,'0'),q=new URLSearchParams(location.search).get('preview');
let note=null,photo=null;
if(S.birthday&&(md===S.birthday||q==='birthday')){note=S.birthday_note;photo=S.birthday_photo}
else if(S.remembrance&&(md===S.remembrance||q==='remembrance')){note=S.remembrance_note;photo=S.remembrance_photo}
if(note){const el=document.getElementById('special');el.hidden=false;el.innerHTML=(photo?'<img src="media/thumb/'+photo+'.webp" alt="">':'')+'<p></p>';el.querySelector('p').textContent=note}})();

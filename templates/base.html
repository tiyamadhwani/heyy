document.addEventListener('DOMContentLoaded',function(){
  const nb=document.getElementById('navbar');
  const st=document.getElementById('scrollTop');
  window.addEventListener('scroll',()=>{
    if(window.scrollY>60){nb&&nb.classList.add('scrolled');st&&st.classList.add('visible');}
    else{nb&&nb.classList.remove('scrolled');st&&st.classList.remove('visible');}
  });
  const tog=document.getElementById('navToggle');
  const menu=document.getElementById('navMenu');
  if(tog&&menu){
    tog.addEventListener('click',()=>{
      menu.classList.toggle('open');
      tog.innerHTML=menu.classList.contains('open')?'<i class="fas fa-times"></i>':'<i class="fas fa-bars"></i>';
    });
    document.addEventListener('click',e=>{
      if(!tog.contains(e.target)&&!menu.contains(e.target)){menu.classList.remove('open');tog.innerHTML='<i class="fas fa-bars"></i>';}
    });
  }
  if(st)st.addEventListener('click',()=>window.scrollTo({top:0,behavior:'smooth'}));
  document.querySelectorAll('.alert').forEach(a=>{setTimeout(()=>a.style.opacity='0',4000);setTimeout(()=>a.remove(),4400);});
  const ci=document.getElementById('barCheckin'),co=document.getElementById('barCheckout');
  const t=new Date().toISOString().split('T')[0],tm=new Date(Date.now()+86400000).toISOString().split('T')[0];
  if(ci){ci.min=t;if(!ci.value)ci.value=t;}
  if(co){co.min=tm;if(!co.value)co.value=tm;}
  if(ci&&co)ci.addEventListener('change',()=>{const d=new Date(ci.value);d.setDate(d.getDate()+1);const s=d.toISOString().split('T')[0];co.min=s;if(co.value<=ci.value)co.value=s;});
  const obs=new IntersectionObserver(e=>e.forEach(x=>{if(x.isIntersecting)x.target.classList.add('visible');}),{threshold:.08});
  document.querySelectorAll('.reveal,.reveal-left,.reveal-right').forEach(el=>obs.observe(el));
  document.querySelectorAll('.gs-btn').forEach(btn=>{
    btn.addEventListener('click',()=>{
      const id=btn.dataset.t||btn.dataset.target;if(!id)return;
      const el=document.getElementById(id);const isA=id.startsWith('a-');
      let v=parseInt(el.textContent)||0;
      if(btn.classList.contains('plus'))v=Math.min(isA?4:3,v+1);
      if(btn.classList.contains('minus'))v=Math.max(isA?1:0,v-1);
      el.textContent=v;
    });
  });
});

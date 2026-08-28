// HERO photography direction: natural people + space + conversation + serendipity.
const heroImg=document.querySelector('.hero-photo img');if(heroImg){heroImg.src='https://drive.google.com/thumbnail?id=1J6Ne_puDhM-7GLyJ1b7n2AMLfLs8ai1u&sz=w2000';heroImg.alt='Garraway Fで人と人が自然につながる風景';heroImg.fetchPriority='high';}
const photo=(id,alt)=>`<figure><img src="https://drive.google.com/thumbnail?id=${id}&sz=w1400" alt="${alt}" loading="lazy"></figure>`;
const statement=document.querySelector('.statement');if(statement){statement.style.display='grid';statement.classList.add('living-photo-story');const old=statement.querySelector('.statement-photo');if(old)old.innerHTML='<img src="https://drive.google.com/thumbnail?id=1Flj3ETVCIChlwQpEvB4BbL19bT3EcQpb&sz=w1800" alt="Garraway Fで自然に生まれる対話" loading="lazy">';}
const facility=document.querySelector('#facility');if(facility&&!facility.querySelector('.living-gallery')){const gallery=document.createElement('div');gallery.className='living-gallery';gallery.innerHTML=`${photo('16bZEROOxM7CvTH3uOLZGiA8TSjNw8Bp3','Garraway Fで集う人たち')}${photo('1fXGYmJIcLKstmGU9TwTfHrdjC3OXh4be','Garraway Fでの対話')}${photo('1Nbri-E3AxcDM-Drofl2_6qf9wRjEqpow','Garraway Fで生まれる活動')}<p class="living-gallery-label">PEOPLE × SPACE / CONVERSATION / ACTION</p>`;facility.querySelector('.facility-grid')?.before(gallery);}
const els=[...document.querySelectorAll('.person,.tiles div,.roles article')];const io=new IntersectionObserver(entries=>entries.forEach(e=>{if(e.isIntersecting){e.target.animate([{opacity:0,transform:'translateY(24px)'},{opacity:1,transform:'translateY(0)'}],{duration:650,easing:'cubic-bezier(.2,.8,.2,1)',fill:'both'});io.unobserve(e.target)}}),{threshold:.15});els.forEach(e=>io.observe(e));

// NEWS & EVENTS — social preview wall.
const newsSection=document.querySelector('#news');
if(newsSection){
 const head=newsSection.querySelector('.news-live-head');
 if(head){const desc=head.querySelector('p:not(.kicker)');if(desc)desc.textContent='各SNSでイベント＆ニュースを発信中。Garraway Fの「今」を見る。';const link=head.querySelector('a');if(link){link.textContent='SOCIAL LIVE';link.href='#social-preview';link.removeAttribute('target');}}
 const frame=newsSection.querySelector('.news-live-frame');
 if(frame){
  frame.id='social-preview';frame.className='social-preview';
  frame.innerHTML=`
  <article class="social-preview-card facebook">
   <div class="social-preview-head"><b>FACEBOOK</b><span>EVENTS & BUSINESS NEWS</span></div>
   <div class="fb-page" data-href="https://www.facebook.com/garrawayf/" data-tabs="timeline" data-width="500" data-height="620" data-small-header="true" data-adapt-container-width="true" data-hide-cover="false" data-show-facepile="false"><blockquote cite="https://www.facebook.com/garrawayf/" class="fb-xfbml-parse-ignore"><a href="https://www.facebook.com/garrawayf/">Garraway F</a></blockquote></div>
   <a class="social-preview-link" href="https://www.facebook.com/garrawayf/" target="_blank" rel="noopener">FACEBOOKを開く ↗</a>
  </article>
  <article class="social-preview-card x">
   <div class="social-preview-head"><b>X</b><span>GARRAWAY F NOW</span></div>
   <a class="twitter-timeline" data-height="620" data-chrome="noheader nofooter noborders transparent" href="https://twitter.com/garraway_f?ref_src=twsrc%5Etfw">Posts by @garraway_f</a>
   <a class="social-preview-link" href="https://x.com/garraway_f" target="_blank" rel="noopener">Xを開く ↗</a>
  </article>
  <article class="social-preview-card instagram instagram-live-card">
   <div class="social-preview-head"><b>INSTAGRAM</b><span>LIVE PROFILE / REELS / PHOTOS</span></div>
   <div class="instagram-profile-preview">
    <div class="instagram-profile-top"><div class="ig-mark">IG</div><div><strong>@garrawayf_lounge</strong><small>GARRAWAY F · FUKUOKA</small></div></div>
    <div class="instagram-preview-grid"><a href="https://www.instagram.com/garrawayf_lounge/" target="_blank" rel="noopener">${photo('1J6Ne_puDhM-7GLyJ1b7n2AMLfLs8ai1u','Garraway Fの人と対話')}</a><a href="https://www.instagram.com/garrawayf_lounge/" target="_blank" rel="noopener">${photo('1Flj3ETVCIChlwQpEvB4BbL19bT3EcQpb','Garraway FのSerendipity')}</a><a href="https://www.instagram.com/garrawayf_lounge/" target="_blank" rel="noopener">${photo('16bZEROOxM7CvTH3uOLZGiA8TSjNw8Bp3','Garraway Fのコミュニティ')}</a><a href="https://www.instagram.com/garrawayf_lounge/" target="_blank" rel="noopener">${photo('1fXGYmJIcLKstmGU9TwTfHrdjC3OXh4be','Garraway Fでの活動')}</a></div>
    <p class="ig-live-note">Instagramは外部サイト上の最新投稿を自動取得する埋め込みを提供していないため、ここでは公式アカウントへのプレビュー導線として表示しています。</p>
   </div>
   <div class="instagram-accounts"><a href="https://www.instagram.com/garrawayf_lounge/" target="_blank" rel="noopener">LOUNGE INSTAGRAM ↗</a><a href="https://www.instagram.com/garrawayf_toshokan/" target="_blank" rel="noopener">LIBRARY INSTAGRAM ↗</a></div>
  </article>`;
 }
 if(!document.querySelector('script[src*="connect.facebook.net"]')){const s=document.createElement('script');s.async=true;s.defer=true;s.crossOrigin='anonymous';s.src='https://connect.facebook.net/ja_JP/sdk.js#xfbml=1&version=v22.0';document.body.appendChild(s);}
 if(!document.querySelector('script[src*="platform.twitter.com/widgets.js"]')){const s=document.createElement('script');s.async=true;s.src='https://platform.twitter.com/widgets.js';document.body.appendChild(s);}
 newsSection.dataset.preserve='social-preview-news-events';
}
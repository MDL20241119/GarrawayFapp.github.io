const els=[...document.querySelectorAll('.person,.tiles div,.roles article')];const io=new IntersectionObserver(entries=>entries.forEach(e=>{if(e.isIntersecting){e.target.animate([{opacity:0,transform:'translateY(24px)'},{opacity:1,transform:'translateY(0)'}],{duration:650,easing:'cubic-bezier(.2,.8,.2,1)',fill:'both'});io.unobserve(e.target)}}),{threshold:.15});els.forEach(e=>io.observe(e));

// NEWS & EVENTS is intentionally preserved as-is.
// Future visual iterations should not rewrite or restyle this section.
const newsSection=document.querySelector('#news');
if(newsSection){newsSection.dataset.preserve='current-news-events';}
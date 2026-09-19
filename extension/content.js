function extract(){return {title:document.title,url:location.href,text:(document.body?.innerText||'').slice(0,4000)}}
chrome.runtime.onMessage.addListener((m,s,send)=>{if(m.type==='extract'){send(extract())}return true})

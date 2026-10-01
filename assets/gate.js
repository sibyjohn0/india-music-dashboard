/* gate.js — email-gated toolkit downloads for Indie Music India.
   View is free; downloading the branded file asks for name + email first, posts the
   lead to a Google Apps Script (which appends to a Google Sheet you own), then
   delivers the file and the editable copy link. Capture is best-effort: if the
   endpoint is unset or fails, the download still works (never trap the user). */
(function () {
  // 1) Paste your deployed Apps Script web-app URL here (ends in /exec). See scripts/toolkit_capture.gs.
  var ENDPOINT = "https://script.google.com/macros/s/AKfycbzl5_Gh0YPEQRy4eH4trTeWUMy1qAMYpMoWzoAcIs7jwMH4sj9kKwlMxF9trJFZgjtl/exec";

  var EMAIL = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

  function esc(s){ return (s||"").replace(/[&<>"]/g,function(c){return {"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c];}); }

  function download(file){
    var a=document.createElement("a");
    a.href=file; a.download=file.split("/").pop(); document.body.appendChild(a); a.click(); a.remove();
  }

  function capture(data){
    if(!ENDPOINT || ENDPOINT.indexOf("REPLACE_WITH")===0) return; // not configured yet
    try{
      fetch(ENDPOINT,{method:"POST",mode:"no-cors",
        headers:{"Content-Type":"application/x-www-form-urlencoded;charset=UTF-8"},
        body:new URLSearchParams(data).toString()});
    }catch(e){/* best-effort */}
  }

  document.querySelectorAll(".dl-gate").forEach(function(g){
    var file=g.dataset.file, type=(g.dataset.type||"file").toUpperCase(),
        copy=g.dataset.copy||"", title=g.dataset.title||document.title;
    g.innerHTML =
      '<h3>Download this template</h3>'+
      '<p>Free. Tell us where to credit it and it is yours, as a neat branded '+esc(type)+'.</p>'+
      '<form class="dl-form" novalidate>'+
        '<input name="name" type="text" placeholder="Your name" autocomplete="name" required>'+
        '<input name="email" type="email" placeholder="Email" autocomplete="email" required>'+
        '<input name="city" type="text" placeholder="City (optional)" autocomplete="address-level2">'+
        '<button type="submit" class="g-btn">Get the template →</button>'+
        '<p class="dl-err" role="alert" style="color:#D8005E;font-size:13px;display:none"></p>'+
      '</form>';
    var form=g.querySelector(".dl-form"), err=g.querySelector(".dl-err");
    form.addEventListener("submit",function(ev){
      ev.preventDefault();
      var name=form.name.value.trim(), email=form.email.value.trim(), city=form.city.value.trim();
      if(!name){ err.textContent="Please add your name."; err.style.display="block"; return; }
      if(!EMAIL.test(email)){ err.textContent="Please enter a valid email."; err.style.display="block"; return; }
      err.style.display="none";
      capture({name:name,email:email,city:city,resource:title,type:type});
      download(file);
      g.innerHTML =
        '<h3>Done. Check your downloads.</h3>'+
        '<p>Your branded '+esc(type)+' is downloading. '+
        (copy?'Prefer to fill it in online? <a href="'+esc(copy)+'" target="_blank" rel="noopener" style="color:var(--accent);font-weight:700">Open an editable copy →</a>':'')+
        '</p>'+
        '<p>Follow the scene on <a href="https://instagram.com/indiemusicindia.co" target="_blank" rel="noopener" style="color:var(--accent);font-weight:700">Instagram</a>, or <a href="https://wa.me/919960025559" target="_blank" rel="noopener" style="color:var(--accent);font-weight:700">WhatsApp us</a> if you want a hand.</p>'+
        '<p style="font-size:13px;color:var(--muted)">It is free to use. Please share the page, not the file.</p>';
    });
  });
})();

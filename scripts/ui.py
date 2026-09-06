"""三頁共用的外殼與 CSS。樣式一律寫在這裡，不要在各頁的 render 裡另發明。

依據 design.md。改樣式前先讀那份。
"""
from __future__ import annotations

import html

FONT = '"Inter",-apple-system,BlinkMacSystemFont,"PingFang TC","Noto Sans TC","Microsoft JhengHei",sans-serif'
MONO = '"JetBrains Mono","SF Mono",Menlo,Consolas,monospace'

PAGES = [
    ("inbox", "職缺收件匣", "▤"),
    ("analysis", "契合度診斷", "◈"),
    ("tracker", "投遞追蹤", "▥"),
]

CSS = """
:root{
 --navy-deep:#0f172a; --navy-midnight:#172554; --navy-slate:#1e293b;
 --navy-cobalt:#1e3a8a; --navy-accent:#0ea5e9; --cyan-spark:#38bdf8;
 --canvas:#f8fafc; --surface:#fff; --surface-alt:#f1f5f9;
 --border:#e2e8f0; --border-strong:#cbd5e1;
 --ink:#0f172a; --ink-body:#334155; --ink-muted:#64748b; --ink-faint:#94a3b8;
 --hi:#059669; --hi-bg:#ecfdf5; --hi-bd:#a7f3d0;
 --mid:#d97706; --mid-bg:#fffbeb; --mid-bd:#fde68a;
 --risk:#dc2626; --risk-bg:#fef2f2; --risk-bd:#fecaca;
 --e1:0 1px 3px 0 rgba(15,23,42,.05),0 1px 2px -1px rgba(15,23,42,.03);
 --e2:0 4px 8px -2px rgba(15,23,42,.06),0 2px 4px -2px rgba(15,23,42,.04);
 --e3:0 12px 24px -4px rgba(15,23,42,.10),0 4px 6px -2px rgba(15,23,42,.04);
 --sidebar:260px;
}
*{box-sizing:border-box}
html,body{margin:0;padding:0}
body{font-family:__FONT__;background:var(--canvas);color:var(--ink-body);
  font-size:14px;line-height:22px;-webkit-font-smoothing:antialiased;
  font-feature-settings:"tnum" 1}
a{color:var(--navy-cobalt);text-decoration:none}
a:hover{text-decoration:underline}
code,.mono{font-family:__MONO__;font-size:12px;letter-spacing:-.01em}

/* ── 外殼 ───────────────────────────── */
.app{display:flex;min-height:100vh}
.side{width:var(--sidebar);flex:0 0 var(--sidebar);background:var(--navy-deep);
  color:#cbd5e1;display:flex;flex-direction:column;position:sticky;top:0;height:100vh}
.brand{display:flex;align-items:center;gap:10px;padding:20px 20px 18px}
.brand .mark{width:30px;height:30px;border-radius:8px;background:var(--navy-accent);
  display:grid;place-items:center;color:#04202e;font-weight:800;font-size:15px}
.brand b{color:#fff;font-size:16px;font-weight:650;letter-spacing:-.01em}
.nav{padding:4px 12px;display:flex;flex-direction:column;gap:2px}
.nav a{display:flex;align-items:center;gap:10px;padding:9px 12px;border-radius:8px;
  color:#94a3b8;font-size:13px;font-weight:500;line-height:18px}
.nav a:hover{background:rgba(255,255,255,.06);color:#e2e8f0;text-decoration:none}
.nav a.on{background:var(--navy-cobalt);color:#fff;box-shadow:inset 0 1px 0 rgba(56,189,248,.5)}
.nav .ic{width:16px;text-align:center;opacity:.9}
.nav .n{margin-left:auto;font-size:11px;font-weight:600;letter-spacing:.04em;
  background:rgba(255,255,255,.10);padding:1px 7px;border-radius:999px}
.nav a.on .n{background:rgba(255,255,255,.22)}
.side .foot{margin-top:auto;padding:14px 20px 18px;border-top:1px solid rgba(255,255,255,.08);
  color:#64748b;font-size:11px;line-height:16px}

.main{flex:1;min-width:0;display:flex;flex-direction:column}
.top{background:var(--surface);border-bottom:1px solid var(--border);
  padding:0 24px;height:60px;display:flex;align-items:center;gap:14px;
  position:sticky;top:0;z-index:20}
.crumb{color:var(--ink-muted);font-size:13px}
.crumb b{color:var(--ink);font-weight:600}
.top .sp{margin-left:auto}
.wrap{padding:22px 24px 56px;max-width:1440px;width:100%}

/* ── 頁首 ───────────────────────────── */
.head{margin-bottom:18px}
.head h1{font-size:28px;line-height:36px;font-weight:700;letter-spacing:-.025em;
  color:var(--ink);margin:0 0 4px}
.head p{margin:0;color:var(--ink-muted);font-size:14px}
.kicker{font-size:11px;font-weight:600;letter-spacing:.04em;text-transform:uppercase;
  color:var(--ink-muted);margin-bottom:6px}

/* ── 卡片 ───────────────────────────── */
.card{background:var(--surface);border:1px solid var(--border);border-radius:8px;
  box-shadow:var(--e1)}
.card.pad{padding:18px 20px}
.card h2{font-size:16px;line-height:24px;font-weight:600;letter-spacing:-.01em;
  color:var(--ink);margin:0 0 12px;display:flex;align-items:center;gap:8px}
.card h2 .sp{margin-left:auto;font-size:12px;font-weight:400;color:var(--ink-muted)}

/* ── 數字卡 ─────────────────────────── */
.metrics{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:14px;
  margin-bottom:18px}
.metric{background:var(--surface);border:1px solid var(--border);border-radius:8px;
  padding:16px 18px;box-shadow:var(--e1)}
.metric .k{font-size:11px;font-weight:600;letter-spacing:.04em;text-transform:uppercase;
  color:var(--ink-muted);display:flex;align-items:center;gap:6px}
.metric .v{font-size:30px;line-height:36px;font-weight:700;letter-spacing:-.03em;
  color:var(--ink);margin:6px 0 2px}
.metric .v small{font-size:13px;font-weight:500;color:var(--ink-muted);letter-spacing:0}
.metric .s{font-size:12px;line-height:18px;color:var(--ink-muted)}

/* ── 按鈕 ───────────────────────────── */
.btn{font:inherit;font-size:13px;font-weight:500;line-height:18px;padding:7px 14px;
  border-radius:8px;border:1px solid transparent;cursor:pointer;display:inline-flex;
  align-items:center;gap:6px;white-space:nowrap}
.btn-p{background:var(--navy-deep);color:#fff}
.btn-p:hover{background:var(--navy-midnight)}
.btn-s{background:#fff;border-color:var(--border-strong);color:var(--navy-slate)}
.btn-s:hover{background:var(--canvas);border-color:#94a3b8}
.btn-a{background:var(--navy-cobalt);color:#fff;box-shadow:inset 0 1px 0 rgba(56,189,248,.45)}
.btn-a:hover{background:#1d4ed8}
.btn-g{background:transparent;color:#475569}
.btn-g:hover{background:var(--surface-alt)}
.btn:disabled{opacity:.45;cursor:not-allowed}
.btn:focus-visible,input:focus-visible,select:focus-visible,textarea:focus-visible{
  outline:none;box-shadow:0 0 0 1px var(--navy-accent),0 0 0 4px rgba(14,165,233,.12)}

/* ── 徽章 ───────────────────────────── */
.badge{display:inline-flex;align-items:center;gap:4px;border-radius:999px;
  padding:2px 9px;font-size:11px;font-weight:600;letter-spacing:.02em;border:1px solid}
.b-hi{background:var(--hi-bg);border-color:var(--hi-bd);color:#065f46}
.b-mid{background:var(--mid-bg);border-color:var(--mid-bd);color:#92400e}
.b-risk{background:var(--risk-bg);border-color:var(--risk-bd);color:#991b1b}
.b-n{background:var(--surface-alt);border-color:var(--border);color:var(--navy-slate)}
.tok{display:inline-block;background:var(--surface-alt);border:1px solid var(--border);
  color:var(--navy-slate);border-radius:999px;padding:2px 9px;margin:2px 3px 2px 0;
  font-family:__MONO__;font-size:11px;line-height:16px}

/* ── 篩選列 ─────────────────────────── */
.bar{display:flex;flex-wrap:wrap;align-items:center;gap:10px;background:var(--surface);
  border:1px solid var(--border);border-radius:8px;padding:12px 14px;margin-bottom:16px;
  box-shadow:var(--e1)}
.bar label{font-size:12px;color:var(--ink-muted);display:inline-flex;align-items:center;gap:6px}
.bar input[type=search],.bar select{font:inherit;font-size:13px;padding:6px 10px;
  border:1px solid var(--border-strong);border-radius:8px;background:#fff;color:var(--ink)}
.bar input[type=search]{width:230px}
.bar input[type=search]::placeholder{color:var(--ink-faint)}
.bar .sp{margin-left:auto;font-size:12px;color:var(--ink-muted)}

/* ── 表格 ───────────────────────────── */
table{border-collapse:collapse;width:100%;font-size:13px;table-layout:fixed;
  background:var(--surface)}
/* 不能用 overflow:hidden 做圓角：它會讓 sticky 的 thead 錯位（表頭掉到第一列下面）。
   改成在角落的儲存格自己做圓角。 */
.tw{border:1px solid var(--border);border-radius:8px;box-shadow:var(--e1);background:var(--surface)}
.tw table{border-radius:8px}
.tw thead th:first-child{border-top-left-radius:8px}
.tw thead th:last-child{border-top-right-radius:8px}
.tw tbody tr:last-child td:first-child{border-bottom-left-radius:8px}
.tw tbody tr:last-child td:last-child{border-bottom-right-radius:8px}
th,td{padding:8px 10px;text-align:left;vertical-align:middle;
  border-bottom:1px solid var(--border);overflow:hidden;text-overflow:ellipsis;
  white-space:nowrap}
th{background:var(--surface-alt);color:var(--ink-muted);font-size:11px;font-weight:600;
  letter-spacing:.04em;text-transform:uppercase;position:sticky;top:60px;z-index:10;
  cursor:pointer;user-select:none;white-space:nowrap;
  box-shadow:inset 0 -1px 0 var(--border)}
th.nosort{cursor:default}
th .ind{color:var(--navy-accent);font-size:10px;margin-left:2px}
tbody tr:last-child td{border-bottom:none}
tr.row:hover{background:#f6fafe}
tr.row.dim{color:var(--ink-faint)}
tr.row.dim a{color:#8fa8c4}
/* 數字欄一律靠右，位數才對得齊 */
td.num,th.rt{font-variant-numeric:tabular-nums;text-align:right;font-weight:600}
td.num .badge{min-width:38px;justify-content:center}
td.ttl a{display:block;overflow:hidden;text-overflow:ellipsis;color:var(--ink);
  font-weight:600;font-size:13px}
td.ttl a:hover{color:var(--navy-cobalt)}
td.co{color:var(--ink-body)}
td.meta{color:var(--ink-muted);font-size:12px}
td.ctr{text-align:center}
tr.det td{background:#fbfcfe;white-space:normal;padding:12px 14px;
  border-bottom:1px solid var(--border)}
tr.det dl{margin:0;display:grid;grid-template-columns:96px 1fr;gap:4px 12px;font-size:12px}
tr.det dt{color:var(--ink-muted);white-space:nowrap}
tr.det dd{margin:0;word-break:break-word;color:var(--ink-body)}
tr.det dd.jd{max-height:5em;overflow:auto}
.toggle{cursor:pointer;color:var(--ink-faint);user-select:none;font-size:11px}
.toggle:hover{color:var(--navy-accent)}

/* 取捨用的兩顆圖示鈕：勾勾＝看過，星星＝儲存 */
td.acts{text-align:right;white-space:nowrap;padding-right:12px}
.ico{font:inherit;font-size:14px;line-height:1;width:26px;height:26px;padding:0;
  border:1px solid var(--border);border-radius:8px;background:#fff;cursor:pointer;
  color:var(--ink-faint);vertical-align:middle}
.ico + .ico{margin-left:6px}
.ico:hover:not(:disabled){border-color:var(--border-strong);color:var(--navy-slate)}
.ico.on{color:var(--hi);border-color:var(--hi-bd);background:var(--hi-bg)}
.ico.star{font-size:15px}
.ico.star.on{color:#b7791f;border-color:var(--mid-bd);background:var(--mid-bg)}
.ico:disabled{cursor:default;opacity:1}

/* 篩選列裡的文字型開關（已看過 N 筆） */
.lnk{font:inherit;font-size:12px;color:var(--ink-muted);background:transparent;
  border:1px solid transparent;border-radius:999px;padding:3px 10px;cursor:pointer}
.lnk:hover{background:var(--surface-alt);color:var(--navy-cobalt)}
.lnk.on{background:var(--surface-alt);color:var(--navy-cobalt);border-color:var(--border)}
.lnk b{font-variant-numeric:tabular-nums}

/* ── 契合度條 ───────────────────────── */
.track{height:6px;background:var(--border);border-radius:999px;overflow:hidden}
.track i{display:block;height:100%;border-radius:999px;background:var(--navy-cobalt)}
.track.hi i{background:var(--hi)} .track.mid i{background:var(--mid)}
.track.risk i{background:var(--risk)}

/* ── 分析卡（第二頁）────────────────── */
.ancol{display:flex;flex-direction:column;gap:14px}
.an{display:grid;grid-template-columns:1fr 300px;gap:22px;background:var(--surface);
  border:1px solid var(--border);border-radius:8px;box-shadow:var(--e1);padding:18px 20px}
.an:hover{border-color:var(--border-strong);box-shadow:var(--e2)}
.an-co{color:var(--ink-muted);font-size:11px;letter-spacing:.02em;margin-bottom:4px}
.an h3{margin:0 0 6px;font-size:16px;line-height:24px;font-weight:600;letter-spacing:-.01em}
.an h3 a{color:var(--ink)} .an h3 a:hover{color:var(--navy-cobalt)}
.an-m{font-size:12px;color:var(--ink-muted);margin-bottom:8px}
.an-m b{color:var(--ink);font-size:13px}
.an-jd{margin:10px 0 0;font-size:12px;line-height:19px;color:var(--ink-muted);
  display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden}
.an-act{display:flex;flex-wrap:wrap;align-items:center;gap:8px;margin-top:14px}
.blk{margin:2px 0 10px;background:var(--risk-bg);border:1px solid var(--risk-bd);
  color:#991b1b;border-radius:8px;padding:7px 11px;font-size:12px;line-height:18px}
.an-r{border-left:1px solid var(--border);padding-left:20px}
.ring{width:104px;height:104px;border-radius:50%;margin:0 auto 8px;display:grid;
  place-content:center;text-align:center;border:8px solid var(--border)}
.ring span{font-size:30px;line-height:32px;font-weight:700;letter-spacing:-.03em;color:var(--ink)}
.ring small{display:block;font-size:11px;color:var(--ink-muted)}
.ring.hi{border-color:var(--hi)} .ring.mid{border-color:var(--mid)}
.ring.risk{border-color:var(--risk)} .ring.n{border-style:dashed}
.verdict{text-align:center;margin-bottom:14px}
.ind{margin-bottom:10px}
.ind-h{display:flex;justify-content:space-between;font-size:11px;color:var(--ink-muted);
  margin-bottom:4px}
.ind-h b{color:var(--ink);font-variant-numeric:tabular-nums}

/* ── 漏斗（第三頁）──────────────────── */
.funnel{display:grid;grid-template-columns:repeat(5,1fr);gap:10px}
.step{background:var(--surface-alt);border:1px solid var(--border);border-radius:8px;
  padding:12px 14px;text-align:center}
.step.last{background:var(--hi-bg);border-color:var(--hi-bd)}
.step .sl{font-size:11px;font-weight:600;letter-spacing:.04em;color:var(--ink-muted)}
.step .sn{font-size:26px;line-height:32px;font-weight:700;letter-spacing:-.03em;
  color:var(--ink);margin:2px 0}
.step.last .sn{color:#065f46}
.step .sp2{font-size:11px;color:var(--ink-muted);font-variant-numeric:tabular-nums}

/* ── 表單控制項 ─────────────────────── */
select.st{font:inherit;font-size:12px;padding:4px 6px;border:1px solid var(--border-strong);
  border-radius:8px;background:#fff;color:var(--ink);width:100%}
textarea.nt{font:inherit;font-size:12px;line-height:18px;width:100%;height:26px;
  border:1px solid var(--border);border-radius:8px;padding:3px 8px;resize:none;
  overflow:hidden;background:#fff;transition:height .12s ease}
textarea.nt:focus{height:72px;overflow:auto;border-color:var(--navy-accent)}
textarea.nt:placeholder-shown{border-color:#eef2f6}
input.dt{font:inherit;font-size:12px;font-variant-numeric:tabular-nums;width:100%;
  padding:4px 8px;border:1px solid var(--border);border-radius:8px;background:#fff;
  color:var(--ink-body);text-align:left}
input.dt:hover{border-color:var(--border-strong)}

/* ── 彈窗 ───────────────────────────── */
dialog.dlg{border:1px solid var(--border-strong);border-radius:8px;padding:0;
  box-shadow:var(--e3);max-width:640px;width:calc(100vw - 48px);max-height:78vh;
  background:var(--surface);color:var(--ink-body)}
dialog.dlg::backdrop{background:rgba(15,23,42,.34)}
.dlg-h{display:flex;align-items:center;gap:10px;padding:16px 20px;
  border-bottom:1px solid var(--border)}
.dlg-h h3{margin:0;font-size:16px;line-height:24px;font-weight:600;color:var(--ink)}
.dlg-h .sp{margin-left:auto}
.dlg-b{padding:6px 20px 16px;overflow:auto;max-height:56vh}
.dlg-b p.hint{color:var(--ink-muted);font-size:12px;margin:10px 0 4px}
.dlg-row{display:flex;align-items:center;gap:12px;padding:10px 0;
  border-bottom:1px solid var(--border)}
.dlg-row:last-child{border-bottom:none}
.dlg-row .g{min-width:0;flex:1}
.dlg-row .t{font-size:13px;font-weight:600;color:var(--ink);white-space:nowrap;
  overflow:hidden;text-overflow:ellipsis}
.dlg-row .m{font-size:12px;color:var(--ink-muted);white-space:nowrap;
  overflow:hidden;text-overflow:ellipsis}
.dlg-empty{padding:28px 0;text-align:center;color:var(--ink-muted);font-size:13px}

/* ── 空狀態 ─────────────────────────── */
.empty{background:var(--surface);border:1px dashed var(--border-strong);border-radius:8px;
  padding:44px 24px;text-align:center;color:var(--ink-muted)}
.empty b{display:block;color:var(--ink);font-size:15px;font-weight:600;margin-bottom:6px}
.empty code{background:var(--surface-alt);border:1px solid var(--border);
  padding:2px 7px;border-radius:6px}

#banner{display:none;margin:0 0 14px;padding:10px 14px;border-radius:8px;
  background:var(--mid-bg);border:1px solid var(--mid-bd);color:#92400e;font-size:13px}

@media (max-width:1180px){ .an{grid-template-columns:1fr}
  .an-r{border-left:0;border-top:1px solid var(--border);padding-left:0;padding-top:16px}
  .funnel{grid-template-columns:repeat(2,1fr)} }
@media (max-width:1100px){
  :root{--sidebar:64px}
  .brand b,.nav a span.lb,.nav .n,.side .foot{display:none}
  .nav a{justify-content:center}
}
"""


def page(title: str, active: str, counts: dict, body: str, script: str = "") -> str:
    """把內容包進共用外殼。active 是 PAGES 的 key。"""
    # 導覽列的 key 是頁名，board.counts() 的 key 是 stage 名，中間差一個 analysis/saved
    stage_key = {"inbox": "inbox", "analysis": "saved", "tracker": "tracker"}
    nav = []
    for key, label, icon in PAGES:
        n = counts.get(stage_key[key], 0)
        on = " on" if key == active else ""
        badge = f"<span class='n'>{n}</span>" if n else ""
        nav.append(
            f"<a class='item{on}' href='{key}.html'><span class='ic'>{icon}</span>"
            f"<span class='lb'>{label}</span>{badge}</a>"
        )
    css = CSS.replace("__FONT__", FONT).replace("__MONO__", MONO)
    cur = next(lb for k, lb, _ in PAGES if k == active)
    return (
        '<!doctype html>\n<html lang="zh-TW"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f"<title>{html.escape(title)}</title>\n<style>{css}</style></head>\n"
        '<body><div class="app">'
        '<aside class="side">'
        '<div class="brand"><span class="mark">N</span><b>NextRole</b></div>'
        f'<nav class="nav">{"".join(nav)}</nav>'
        f'<div class="foot">共 {counts.get("_total", 0)} 筆職缺<br>資料在 ~/.nextrole/</div>'
        "</aside>"
        '<div class="main">'
        f'<header class="top"><span class="crumb">NextRole › <b>{html.escape(cur)}</b></span>'
        '<span class="sp"></span></header>'
        f'<div class="wrap"><div id="banner"></div>{body}</div>'
        "</div></div>"
        f"<script>{SHARED_JS}{script}</script></body></html>"
    )


# 三頁共用：寫回、展開、排序
SHARED_JS = """
window.NR = (function(){
  var banner=document.getElementById('banner');
  function fallback(id,field,value){
    banner.style.display='block';
    banner.innerHTML='⚠️ 連不上本機服務，改動只暫存在瀏覽器裡。請用 '+
      '<code>cd ~/.nextrole/bin &amp;&amp; uv run serve.py</code> 開這一頁。';
    try{
      var k='nextrole:pending', p=JSON.parse(localStorage.getItem(k)||'{}');
      p[id]=p[id]||{}; p[id][field]=value; localStorage.setItem(k,JSON.stringify(p));
    }catch(e){}
  }
  function flash(el,ok){
    if(!el) return;
    el.style.boxShadow = ok? '0 0 0 2px #059669':'0 0 0 2px #d97706';
    setTimeout(function(){el.style.boxShadow='';},600);
  }
  function patch(id,field,value,el,after){
    var body={}; body[field]=value;
    return fetch('/api/job/'+id,{method:'PATCH',
        headers:{'Content-Type':'application/json'},body:JSON.stringify(body)})
      .then(function(r){ if(!r.ok) throw new Error(r.status); return r.json(); })
      .then(function(j){ flash(el,true); if(after) after(j); })
      .catch(function(){ fallback(id,field,value); flash(el,false); });
  }
  function sortable(tableId,rows){
    var tbody=document.querySelector('#'+tableId+' tbody'), dir={};
    document.querySelectorAll('#'+tableId+' th[data-k]').forEach(function(th){
      th.onclick=function(){
        var k=th.dataset.k, num=th.dataset.num==='1';
        dir[k]=!dir[k]; var sign=dir[k]?1:-1;
        document.querySelectorAll('#'+tableId+' th .ind').forEach(function(s){s.textContent='';});
        var ind=th.querySelector('.ind'); if(ind) ind.textContent=dir[k]?'▲':'▼';
        var pairs=rows.map(function(r){return [r, r.nextElementSibling];});
        pairs.sort(function(a,b){
          var x=a[0].dataset[k]||'', y=b[0].dataset[k]||'';
          return num ? (parseFloat(x||-1)-parseFloat(y||-1))*sign
                     : x.localeCompare(y,'zh-Hant')*sign;
        });
        pairs.forEach(function(p){ tbody.appendChild(p[0]);
          if(p[1]&&p[1].classList.contains('det')) tbody.appendChild(p[1]); });
      };
    });
  }
  function expanders(){
    document.querySelectorAll('.toggle').forEach(function(t){
      t.onclick=function(){
        var d=t.closest('tr').nextElementSibling;
        if(!d||!d.classList.contains('det')) return;
        var open=d.style.display==='table-row';
        d.style.display=open?'none':'table-row';
        t.textContent=open?'▶':'▼';
      };
    });
  }
  function wireRestore(b){
    b.onclick=function(){
      b.disabled=true; b.textContent='處理中…';
      // 放回去牽動三頁的計數，重載最省事也最不會各說各話
      patch(b.dataset.id, b.dataset.field, b.dataset.value==='1', b,
            function(){ location.reload(); });
    };
  }
  function dialogs(){
    document.querySelectorAll('[data-open]').forEach(function(b){
      b.onclick=function(){ document.getElementById(b.dataset.open).showModal(); };
    });
    document.querySelectorAll('[data-close]').forEach(function(b){
      b.onclick=function(){ b.closest('dialog').close(); };
    });
    document.querySelectorAll('.dlg-restore').forEach(wireRestore);
  }
  // 收起來的東西要「當下」就進彈窗。彈窗內容是伺服器在頁面載入時畫的，
  // 不同步加進去的話，使用者剛按掉的那一筆要重整才看得到 —— 等於沒作用。
  function stash(did, info){
    var dlg=document.getElementById(did); if(!dlg) return;
    var body=dlg.querySelector('.dlg-b');
    var blank=body.querySelector('.dlg-empty'); if(blank) blank.remove();
    var row=document.createElement('div');
    row.className='dlg-row';
    row.innerHTML='<div class="g"><div class="t"></div><div class="m"></div></div>';
    row.querySelector('.t').textContent=info.title;
    row.querySelector('.m').textContent=info.meta;
    var btn=document.createElement('button');
    btn.className='btn btn-s dlg-restore';
    btn.dataset.id=info.id; btn.dataset.field=info.field; btn.dataset.value='0';
    btn.textContent=info.label;
    wireRestore(btn);
    row.appendChild(btn);
    body.appendChild(row);
    var n=body.querySelectorAll('.dlg-row').length;
    var h=dlg.querySelector('.dlg-n'); if(h) h.textContent=n;
    var opener=document.querySelector('[data-open="'+did+'"] b');
    if(opener) opener.textContent=n;
  }
  return {patch:patch, sortable:sortable, expanders:expanders,
          dialogs:dialogs, stash:stash};
})();
"""

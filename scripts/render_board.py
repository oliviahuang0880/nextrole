#!/usr/bin/env python3
"""把 board.json 畫成一頁可篩選／可排序／可改狀態的資料表。

⚠️ 一定要透過 serve.py 開（http://127.0.0.1:…）。
   直接用 file:// 開，職缺連結會空白，狀態也存不回去。
"""
from __future__ import annotations

import datetime as dt
import html
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import board as bd  # noqa: E402
import store  # noqa: E402

CSS = """
 body{font-family:-apple-system,"PingFang TC","Microsoft JhengHei",sans-serif;margin:24px;color:#1a1a1a}
 h1{font-size:22px;margin-bottom:4px}
 .meta{color:#666;font-size:13px}
 .bar{margin:14px 0;padding:12px;background:#f6f8fa;border:1px solid #e3e3e3;border-radius:8px}
 .bar label{font-size:13px;margin-right:14px;display:inline-block;line-height:2}
 .bar input[type=search]{padding:4px 8px;border:1px solid #ccc;border-radius:6px;font-size:13px;width:220px}
 .bar select{padding:3px 6px;border:1px solid #ccc;border-radius:6px;font-size:13px}
 table{border-collapse:collapse;width:100%;font-size:13px;margin-top:8px}
 th,td{border:1px solid #e3e3e3;padding:6px 8px;text-align:left;vertical-align:top}
 th{background:#f6f8fa;position:sticky;top:0;cursor:pointer;user-select:none;white-space:nowrap}
 th.nosort{cursor:default}
 th .ind{color:#0b66c2;font-size:11px}
 td.score{font-weight:700;text-align:center;background:#f0f7ff}
 td.fit{text-align:center;font-weight:700}
 td.new,td.remote,td.block{text-align:center}
 td.kw{color:#0a7a3f;font-size:12px;max-width:260px}
 tr.job:hover{background:#fafafa}
 tr.detail td{background:#fcfcfd;color:#444;font-size:12px}
 tr.detail dl{margin:0;display:grid;grid-template-columns:88px 1fr;gap:2px 10px}
 tr.detail dt{color:#888} tr.detail dd{margin:0}
 a{color:#0b66c2;text-decoration:none} a:hover{text-decoration:underline}
 .pill{display:inline-block;background:#0b66c2;color:#fff;border-radius:12px;padding:2px 10px;font-size:12px}
 .pill.g{background:#0a7a3f} .pill.n{background:#8a8a8a}
 select.st{font-size:12px;padding:2px 4px;border:1px solid #ccc;border-radius:6px}
 select.st[data-v=applied]{background:#eef6ff} select.st[data-v=interviewing]{background:#fff6e0}
 select.st[data-v=offer]{background:#e8f8ee} select.st[data-v=rejected],select.st[data-v=skipped]{color:#999}
 textarea.nt{font:inherit;font-size:12px;width:150px;height:34px;border:1px solid #ddd;border-radius:6px;padding:3px}
 .v投{color:#0a7a3f} .v邊緣{color:#b26a00} .v不投{color:#999}
 #banner{display:none;margin:10px 0;padding:8px 12px;border-radius:6px;background:#fff3cd;border:1px solid #ffe08a;font-size:13px}
 .toggle{cursor:pointer;color:#0b66c2}
"""

JS = """
(function(){
  var rows = Array.prototype.slice.call(document.querySelectorAll('tr.job'));
  var q=document.getElementById('q'), fsrc=document.getElementById('fsrc'),
      fst=document.getElementById('fst'), fmin=document.getElementById('fmin'),
      fnew=document.getElementById('fnew'), funrated=document.getElementById('funrated'),
      cnt=document.getElementById('cnt'), banner=document.getElementById('banner');

  function detailOf(r){ return r.nextElementSibling; }

  function apply(){
    var text=(q.value||'').trim().toLowerCase(), src=fsrc.value, st=fst.value,
        min=parseInt(fmin.value||'0',10), n=0;
    rows.forEach(function(r){
      var ok = true;
      if(src && r.dataset.src!==src) ok=false;
      if(ok && st && r.dataset.status!==st) ok=false;
      if(ok && min && parseInt(r.dataset.score,10)<min) ok=false;
      if(ok && fnew.checked && r.dataset.isnew!=='1') ok=false;
      if(ok && funrated.checked && r.dataset.rated==='1') ok=false;
      if(ok && text && r.dataset.hay.indexOf(text)===-1) ok=false;
      r.style.display = ok?'':'none';
      var d=detailOf(r); if(d&&d.classList.contains('detail')&&!ok) d.style.display='none';
      if(ok) n++;
    });
    cnt.textContent='　顯示 '+n+' / '+rows.length+' 筆';
  }
  [q,fsrc,fst,fmin,fnew,funrated].forEach(function(el){
    el.addEventListener(el.tagName==='INPUT'&&el.type!=='checkbox'?'input':'change', apply);
  });

  // 排序
  var tbody=document.querySelector('#board tbody'), dir={};
  document.querySelectorAll('#board th[data-k]').forEach(function(th){
    th.onclick=function(){
      var k=th.dataset.k, num=th.dataset.num==='1';
      dir[k]=!dir[k]; var sign=dir[k]?1:-1;
      document.querySelectorAll('#board th .ind').forEach(function(s){s.textContent='';});
      var ind=th.querySelector('.ind'); if(ind) ind.textContent=dir[k]?'▲':'▼';
      var pairs=rows.map(function(r){return [r, detailOf(r)];});
      pairs.sort(function(a,b){
        var x=a[0].dataset[k]||'', y=b[0].dataset[k]||'';
        if(num){ return (parseFloat(x||-1)-parseFloat(y||-1))*sign; }
        return x.localeCompare(y,'zh-Hant')*sign;
      });
      pairs.forEach(function(p){ tbody.appendChild(p[0]); if(p[1]) tbody.appendChild(p[1]); });
    };
  });

  // 展開細節
  document.querySelectorAll('.toggle').forEach(function(t){
    t.onclick=function(){
      var d=detailOf(t.closest('tr'));
      if(!d) return;
      var open = d.style.display!=='none' && d.style.display!=='';
      d.style.display = open?'none':'table-row';
      t.textContent = open?'▸':'▾';
    };
  });

  // 寫回
  var offline=false;
  function fallback(id,field,value){
    offline=true; banner.style.display='block';
    try{
      var k='nextrole:pending';
      var p=JSON.parse(localStorage.getItem(k)||'{}');
      p[id]=p[id]||{}; p[id][field]=value;
      localStorage.setItem(k, JSON.stringify(p));
      document.getElementById('pending').textContent=JSON.stringify(p);
    }catch(e){}
  }
  function push(id, field, value, el){
    var body={}; body[field]=value;
    fetch('/api/job/'+id, {method:'PATCH', headers:{'Content-Type':'application/json'},
                           body:JSON.stringify(body)})
      .then(function(r){ if(!r.ok) throw new Error(r.status); return r.json(); })
      .then(function(){ el.style.outline='2px solid #0a7a3f';
                        setTimeout(function(){el.style.outline='';}, 600); })
      .catch(function(){ fallback(id, field, value);
                         el.style.outline='2px solid #b26a00';
                         setTimeout(function(){el.style.outline='';}, 600); });
  }
  document.querySelectorAll('select.st').forEach(function(s){
    s.onchange=function(){
      s.dataset.v=s.value;
      var tr=s.closest('tr'); tr.dataset.status=s.value;
      push(s.dataset.id,'status',s.value,s); apply();
    };
  });
  document.querySelectorAll('textarea.nt').forEach(function(t){
    t.onchange=function(){ push(t.dataset.id,'notes',t.value,t); };
  });

  apply();
})();
"""


def _fit_cell(fit: dict) -> tuple[str, str, str]:
    total = fit.get("total")
    if total is None:
        return "<span class='pill n'>未評</span>", "", "-1"
    verdict = fit.get("verdict") or ""
    return f"<span class='v{html.escape(verdict)}'>{total}／13</span>", verdict, str(total)


def render(b: dict, path: str, threshold: int) -> str:
    now = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    cnt = bd.counts(b)
    recs = sorted(
        b["jobs"].items(),
        key=lambda kv: (
            kv[1].get("fit", {}).get("total") or -1,
            kv[1].get("eval", {}).get("score") or 0,
        ),
        reverse=True,
    )

    sources = sorted({r.get("job", {}).get("source", "") for _, r in recs} - {""})
    src_opts = "".join(f"<option value='{html.escape(s)}'>{html.escape(s)}</option>" for s in sources)
    st_opts = "".join(
        f"<option value='{s}'>{bd.STATUS_ZH[s]}</option>" for s in bd.STATUSES
    )

    body = []
    for jid, rec in recs:
        j, e = rec.get("job", {}), rec.get("eval", {})
        fit = rec.get("fit", {}) or {}
        art = rec.get("artifacts", {}) or {}
        title, company = j.get("title", ""), j.get("company", "")
        src, loc, url = j.get("source", ""), j.get("location", ""), j.get("url", "")
        score = e.get("score", 0)
        status = rec.get("status", "new")
        fit_html, verdict, fit_sort = _fit_cell(fit)
        blocked = fit.get("hard_blocker")
        block_cell = "🚫" if blocked else ("—" if blocked is False else "")
        kw = "、".join((e.get("matched_pos") or [])[:8])
        link = (
            f'<a href="{html.escape(url)}" target="_blank" rel="noopener noreferrer">{html.escape(title)}</a>'
            if url else html.escape(title)
        )
        outs = []
        for key, label in (("resume", "履歷"), ("cover_letter", "求職信"), ("qa", "面試題"), ("sheet_tab", "頁籤")):
            if art.get(key):
                outs.append(f"<span title='{html.escape(str(art[key]))}'>{label}✅</span>")
        hay = " ".join([title, company, loc, src, kw]).lower()

        sel = "".join(
            f"<option value='{s}'{' selected' if s == status else ''}>{bd.STATUS_ZH[s]}</option>"
            for s in bd.STATUSES
        )
        body.append(
            f"<tr class='job' data-src='{html.escape(src)}' data-status='{status}' "
            f"data-score='{score}' data-fit='{fit_sort}' data-isnew='{1 if status == 'new' else 0}' "
            f"data-rated='{1 if fit.get('total') is not None else 0}' "
            f"data-title='{html.escape(title)}' data-company='{html.escape(company)}' "
            f"data-hay='{html.escape(hay)}'>"
            f"<td class='new'><span class='toggle'>▸</span></td>"
            f"<td><select class='st' data-id='{jid}' data-v='{status}'>{sel}</select></td>"
            f"<td class='score'>{score}</td>"
            f"<td class='fit'>{fit_html}</td>"
            f"<td class='block'>{block_cell}</td>"
            f"<td>{link}</td><td>{html.escape(company)}</td><td>{html.escape(src)}</td>"
            f"<td class='remote'>{'✅' if j.get('remote') else ''}</td>"
            f"<td>{html.escape(loc)}</td>"
            f"<td class='kw'>{html.escape(kw)}</td>"
            f"<td>{' '.join(outs)}</td>"
            f"<td><textarea class='nt' data-id='{jid}' placeholder='備註'>"
            f"{html.escape(rec.get('notes', ''))}</textarea></td>"
            f"</tr>"
        )
        jd = (j.get("description") or "").strip().replace("\n", " ")[:400]
        neg = "、".join(e.get("matched_neg") or []) or "無"
        body.append(
            f"<tr class='detail' style='display:none'><td colspan='13'><dl>"
            f"<dt>子分</dt><dd>技能 {e.get('score_method2', '-')}／天賦 {e.get('score_method1', '-')}"
            f"／扣分 {e.get('penalty', 0)}</dd>"
            f"<dt>負向命中</dt><dd>{html.escape(neg)}</dd>"
            f"<dt>適合度</dt><dd>{'產業 %s／重疊 %s／條件 %s　%s' % (fit.get('industry', '-'), fit.get('overlap', '-'), fit.get('condition', '-'), html.escape(fit.get('blocker_note') or '')) if fit.get('total') is not None else '尚未評分'}</dd>"
            f"<dt>薪資</dt><dd>{html.escape(j.get('salary') or '未列')}</dd>"
            f"<dt>JD</dt><dd>{html.escape(jd)}…</dd>"
            f"</dl></td></tr>"
        )

    head = (
        "<tr>"
        "<th class='nosort'></th><th class='nosort'>狀態</th>"
        "<th data-k='score' data-num='1'>機器分<span class='ind'></span></th>"
        "<th data-k='fit' data-num='1'>適合度<span class='ind'></span></th>"
        "<th class='nosort'>硬門檻</th>"
        "<th data-k='title'>職缺<span class='ind'></span></th>"
        "<th data-k='company'>公司<span class='ind'></span></th>"
        "<th data-k='src'>來源<span class='ind'></span></th>"
        "<th class='nosort'>遠端</th><th class='nosort'>地點</th>"
        "<th class='nosort'>命中關鍵字</th><th class='nosort'>產出</th><th class='nosort'>備註</th>"
        "</tr>"
    )

    summary = "　".join(
        f"{bd.STATUS_ZH[s]} {cnt[s]}" for s in bd.STATUSES if cnt[s]
    ) or "還沒有職缺"

    doc = (
        '<!doctype html>\n<html lang="zh-TW"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f"<title>NextRole 職缺看板 {now}</title>\n<style>{CSS}</style></head><body>\n"
        "<h1>NextRole 職缺看板</h1>\n"
        f'<p class="meta">更新於 {now}　|　共 {cnt["_total"]} 筆　|　'
        f'<span class="pill">已評適合度 {cnt["_rated"]} 筆</span>　'
        f'<span class="pill g">投遞門檻 {threshold} 分</span></p>\n'
        f'<p class="meta">{summary}</p>\n'
        '<div id="banner">⚠️ 連不上本機服務，改動只暫存在瀏覽器裡。'
        '請用 <code>uv run serve.py</code> 開這一頁，或把下面這段貼給 Claude 補寫回：'
        '<br><code id="pending"></code></div>\n'
        '<div class="bar">'
        '<label>搜尋 <input type="search" id="q" placeholder="職缺／公司／地點／關鍵字"></label>'
        f'<label>來源 <select id="fsrc"><option value="">全部</option>{src_opts}</select></label>'
        f'<label>狀態 <select id="fst"><option value="">全部</option>{st_opts}</select></label>'
        '<label>機器分 ≥ <select id="fmin">'
        '<option value="0">不限</option><option value="40">40</option>'
        '<option value="60">60</option><option value="80">80</option></select></label>'
        '<label><input type="checkbox" id="fnew"> 只看未處理</label>'
        '<label><input type="checkbox" id="funrated"> 只看未評適合度</label>'
        '<span id="cnt" class="meta"></span></div>\n'
        f'<table id="board"><thead>{head}</thead><tbody>\n'
        + ("\n".join(body) if body else "<tr><td colspan='13'>還沒有職缺。先跑 <code>/nextrole:search</code>。</td></tr>")
        + f"\n</tbody></table>\n<script>{JS}</script>\n</body></html>"
    )
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(doc)
    return path


def main():
    b = bd.load()
    cfg = store.load_config()
    path = os.path.join(store.OUTPUT, "board.html")
    render(b, path, cfg["fit_threshold"])
    c = bd.counts(b)
    print(f"已產生 {path}（{c['_total']} 筆，已評適合度 {c['_rated']} 筆）")
    print("用 `uv run serve.py` 開，不要用 file:// — 連結會空白、狀態也存不回去。")


if __name__ == "__main__":
    main()

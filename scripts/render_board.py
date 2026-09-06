#!/usr/bin/env python3
"""把 board.json 畫成三頁：職缺收件匣 / 適合度分析 / 投遞追蹤。

每一頁只回答一個問題，流動方向是單向的（見 design.md）。

⚠️ 一定要透過 serve.py 開（http://127.0.0.1:…）。
   直接用 file:// 開，職缺連結會空白，改動也存不回去。
"""
from __future__ import annotations

import html
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import board as bd  # noqa: E402
import store  # noqa: E402
import ui  # noqa: E402

E = html.escape


# ── 共用小工具 ──────────────────────────────────────────────
def score_class(score: int) -> str:
    return "hi" if score >= 75 else ("mid" if score >= 50 else "risk")


def verdict_class(rec: dict, threshold: int) -> str:
    fit = rec.get("fit") or {}
    if fit.get("total") is None:
        return "n"
    if fit.get("hard_blocker"):
        return "risk"
    return {"投": "hi", "邊緣": "mid", "不投": "risk"}.get(fit.get("verdict"), "n")


def job_link(j: dict) -> str:
    title, url = j.get("title", ""), j.get("url", "")
    return (f'<a href="{E(url)}" target="_blank" rel="noopener noreferrer">{E(title)}</a>'
            if url else E(title))


def empty(title: str, hint: str) -> str:
    return f"<div class='empty'><b>{title}</b>{hint}</div>"


def dialog(did: str, title: str, hint: str, rows: list[tuple[str, dict]],
           field: str, btn: str) -> str:
    """列出被收起來的職缺，每筆可以放回去。"""
    if rows:
        items = "".join(
            f"<div class='dlg-row'><div class='g'>"
            f"<div class='t'>{E(r['job'].get('title',''))}</div>"
            f"<div class='m'>{E(r['job'].get('company',''))}　·　"
            f"{E(r['job'].get('location',''))}　·　評分 {r['eval'].get('score',0)}</div></div>"
            f"<button class='btn btn-s dlg-restore' data-id='{jid}' "
            f"data-field='{field}' data-value='0'>{btn}</button></div>"
            for jid, r in rows
        )
    else:
        items = f"<div class='dlg-empty'>目前沒有{title}的職缺。</div>"
    return (
        f"<dialog class='dlg' id='{did}'>"
        f"<div class='dlg-h'><h3>{title}（{len(rows)}）</h3>"
        f"<span class='sp'></span>"
        f"<button class='btn btn-g' data-close>關閉</button></div>"
        f"<div class='dlg-b'><p class='hint'>{hint}</p>{items}</div></dialog>"
    )


def metric(k: str, v: str, sub: str = "") -> str:
    return (f"<div class='metric'><div class='k'>{k}</div><div class='v'>{v}</div>"
            f"<div class='s'>{sub}</div></div>")


# ── ① 職缺收件匣 ────────────────────────────────────────────
def render_inbox(b: dict, cfg: dict, path: str) -> str:
    cnt = bd.counts(b)
    # 按了勾勾的不進表格，只進彈窗
    dismissed = sorted(bd.dismissed(b),
                       key=lambda kv: kv[1]["eval"].get("score", 0), reverse=True)
    dismissed_ids = {jid for jid, _ in dismissed}
    inbox = sorted(
        ((j, r) for j, r in b["jobs"].items()
         if not r.get("status") and j not in dismissed_ids),
        key=lambda kv: kv[1].get("eval", {}).get("score", 0), reverse=True,
    )

    srcs = sorted({r["job"].get("source", "") for _, r in inbox} - {""})
    src_opts = "".join(f"<option value='{E(s)}'>{E(s)}</option>" for s in srcs)

    body = []
    for jid, rec in inbox:
        j, e = rec["job"], rec["eval"]
        sc = e.get("score", 0)
        saved = bool(rec.get("saved"))
        all_kw = e.get("matched_pos") or []
        kw = "、".join(all_kw[:3]) + ("…" if len(all_kw) > 3 else "")
        hay = " ".join([j.get("title", ""), j.get("company", ""),
                        j.get("location", ""), j.get("source", ""), kw]).lower()
        body.append(
            f"<tr class='row' data-id='{jid}' data-saved='{int(saved)}' "
            f"data-score='{sc}' data-src='{E(j.get('source',''))}' "
            f"data-title='{E(j.get('title',''))}' data-company='{E(j.get('company',''))}' "
            f"data-hay='{E(hay)}'>"
            f"<td class='ctr'><span class='toggle'>▶</span></td>"
            f"<td class='num'><span class='badge b-{score_class(sc)}'>{sc}</span></td>"
            f"<td class='ttl' title='{E(j.get('title',''))}'>{job_link(j)}</td>"
            f"<td class='co' title='{E(j.get('company',''))}'>{E(j.get('company',''))}</td>"
            f"<td class='meta'>{E(j.get('source',''))}</td>"
            f"<td class='ctr'>{'✓' if j.get('remote') else ''}</td>"
            f"<td class='meta' title='{E(j.get('location',''))}'>{E(j.get('location',''))}</td>"
            f"<td class='meta' title='{E('、'.join(all_kw))}'>{E(kw)}</td>"
            f"<td class='acts'>"
            f"<button class='ico act-seen' data-id='{jid}' "
            f"title='看過了，從清單收起來'>✓</button>"
            f"<button class='ico star act-save{' on' if saved else ''}' data-id='{jid}' "
            f"title='{'已儲存' if saved else '儲存，進到契合度診斷'}'"
            f"{' disabled' if saved else ''}>{'★' if saved else '☆'}</button>"
            f"</td></tr>"
        )
        jd = (j.get("description") or "").strip().replace("\n", " ")[:400]
        body.append(
            f"<tr class='det' style='display:none'><td colspan='9'><dl>"
            f"<dt>子分</dt><dd>技能 {e.get('score_method2','-')}／天賦 {e.get('score_method1','-')}"
            f"　扣分 {e.get('penalty',0)}</dd>"
            f"<dt>命中關鍵字</dt><dd>{''.join(f'<span class=tok>{E(k)}</span>' for k in all_kw) or '無'}</dd>"
            f"<dt>負向命中</dt><dd>{E('、'.join(e.get('matched_neg') or []) or '無')}</dd>"
            f"<dt>JD</dt><dd class='jd'>{E(jd)}…</dd></dl></td></tr>"
        )

    table = (
        "<div class='tw'><table id='t'><colgroup>"
        "<col style='width:30px'><col style='width:72px'><col style='width:246px'>"
        "<col style='width:126px'><col style='width:72px'><col style='width:48px'>"
        "<col style='width:112px'><col><col style='width:84px'>"
        "</colgroup><thead><tr>"
        "<th class='nosort'></th>"
        "<th data-k='score' data-num='1' class='rt'>評分<span class='ind'></span></th>"
        "<th data-k='title'>職缺<span class='ind'></span></th>"
        "<th data-k='company'>公司<span class='ind'></span></th>"
        "<th data-k='src'>來源<span class='ind'></span></th>"
        "<th class='nosort'>遠端</th><th class='nosort'>地點</th>"
        "<th class='nosort'>命中詞</th><th class='nosort'></th>"
        "</tr></thead><tbody>" + "\n".join(body) + "</tbody></table></div>"
    ) if inbox else empty(
        "收件匣是空的",
        "還沒有搜尋結果。跑 <code>/nextrole:search</code> 抓一批職缺回來。"
    )

    content = (
        "<div class='head'><div class='kicker'>第一步 · 取捨</div>"
        "<h1>職缺收件匣</h1>"
        "<p>這批搜尋結果裡，哪些值得留下？評分只看關鍵字命中，"
        "用它判斷搜尋詞抓得準不準，不是判斷該不該投。"
        "<b>✓</b> 收起來、<b>☆</b> 存進契合度診斷。</p></div>"
        "<div class='bar'>"
        "<label>搜尋 <input type='search' id='q' placeholder='職缺／公司／地點／關鍵字'></label>"
        f"<label>來源 <select id='fsrc'><option value=''>全部</option>{src_opts}</select></label>"
        "<label>評分 ≥ <select id='fmin'><option value='0'>不限</option>"
        "<option value='50'>50</option><option value='75'>75</option></select></label>"
        f"<button class='lnk' data-open='seenDlg'>已看過 <b>{len(dismissed)}</b> 筆</button>"
        "<span class='sp' id='cnt'></span></div>"
        + table
        + dialog("seenDlg", "已看過", "按了 ✓ 收起來的職缺。下次自動搜尋也不會再出現。"
                 "想放回清單就按右邊的按鈕。", dismissed, "seen", "放回清單")
    )

    js = """
    var rows=[].slice.call(document.querySelectorAll('tr.row'));
    var q=document.getElementById('q'),fsrc=document.getElementById('fsrc'),
        fmin=document.getElementById('fmin'),cnt=document.getElementById('cnt');
    function apply(){
      var t=(q.value||'').trim().toLowerCase(),s=fsrc.value,
          m=parseInt(fmin.value||'0',10),n=0;
      rows.forEach(function(r){
        var ok = r.dataset.gone!=='1';
        if(ok&&s&&r.dataset.src!==s) ok=false;
        if(ok&&m&&parseInt(r.dataset.score,10)<m) ok=false;
        if(ok&&t&&r.dataset.hay.indexOf(t)===-1) ok=false;
        r.style.display=ok?'':'none';
        var d=r.nextElementSibling;
        if(d&&d.classList.contains('det')&&!ok) d.style.display='none';
        if(ok)n++;
      });
      cnt.textContent='顯示 '+n+' 筆';
    }
    [q,fsrc,fmin].forEach(function(el){
      el.addEventListener(el.type==='search'?'input':'change',apply);});

    function rowOf(id){return rows.filter(function(r){return r.dataset.id===id;})[0];}
    // ✓ 看過 → 該列立刻消失。要放回來得從篩選列的「已看過」彈窗。
    document.querySelectorAll('.act-seen').forEach(function(btn){
      btn.onclick=function(){
        var r=rowOf(btn.dataset.id);
        NR.patch(btn.dataset.id,'seen',true,btn,function(){
          r.dataset.gone='1'; apply();
        });
      };
    });
    // ☆ 儲存 → 只做儲存。不碰「看過」，那是 ✓ 的事，該列也留著。
    document.querySelectorAll('.act-save').forEach(function(btn){
      btn.onclick=function(){
        if(btn.disabled) return;
        rowOf(btn.dataset.id).dataset.saved='1';
        NR.patch(btn.dataset.id,'saved',true,btn,function(){
          btn.textContent='★'; btn.classList.add('on');
          btn.disabled=true; btn.title='已儲存（要取消請到契合度診斷頁）';
        });
      };
    });
    NR.sortable('t',rows); NR.expanders(); NR.dialogs(); apply();
    """
    doc = ui.page("職缺收件匣 · NextRole", "inbox", cnt, content, js)
    return _write(path, doc)


# ── ② 適合度分析 ────────────────────────────────────────────
IND = [("industry", "產業關係", 4), ("overlap", "職務重疊", 4), ("condition", "條件符合", 5)]


def render_analysis(b: dict, cfg: dict, path: str) -> str:
    cnt = bd.counts(b)
    threshold = cfg["fit_threshold"]
    saved = bd.in_stage(b, "saved")
    saved.sort(key=lambda kv: (kv[1].get("fit", {}).get("total") or -1,
                               kv[1]["eval"].get("score", 0)), reverse=True)
    removed = sorted(bd.removed_from_analysis(b),
                     key=lambda kv: kv[1]["eval"].get("score", 0), reverse=True)

    rated = [r for _, r in saved if (r.get("fit") or {}).get("total") is not None]
    go = [r for r in rated if r["fit"]["verdict"] == "投"]

    cards = []
    for jid, rec in saved:
        j, e = rec["job"], rec["eval"]
        fit = rec.get("fit") or {}
        total = fit.get("total")
        vc = verdict_class(rec, threshold)
        blocked = fit.get("hard_blocker")

        if total is None:
            score_block = (
                "<div class='ring n'><span>—</span><small>未評分</small></div>"
                "<p class='meta' style='margin:10px 0 0;font-size:12px;color:var(--ink-muted)'>"
                "還沒診斷。跟 Claude 說「幫我評這筆」，或用 <code>/nextrole:board</code>。</p>"
            )
            bars = ""
        else:
            score_block = (
                f"<div class='ring {vc}'><span>{total}</span><small>／13</small></div>"
                f"<div class='verdict'><span class='badge b-{vc}'>"
                f"{E(fit.get('verdict') or '')}</span></div>"
            )
            bars = "".join(
                f"<div class='ind'><div class='ind-h'><span>{label}</span>"
                f"<b>{fit.get(key)}／{mx}</b></div>"
                f"<div class='track {vc}'><i style='width:{100*(fit.get(key) or 0)/mx:.0f}%'></i></div></div>"
                for key, label, mx in IND
            )

        blocker = (
            f"<div class='blk'>🚫 硬門檻：{E(fit.get('blocker_note') or '未註明')}</div>"
            if blocked else ""
        )
        art = rec.get("artifacts") or {}
        done = [lb for k, lb in (("resume", "履歷"), ("cover_letter", "求職信"),
                                 ("qa", "面試題")) if art.get(k)]
        all_kw = e.get("matched_pos") or []
        jd = (j.get("description") or "").strip().replace("\n", " ")[:220]
        jd_html = f"<p class='an-jd'>{E(jd)}…</p>" if jd else ""

        cards.append(
            f"<article class='an' data-id='{jid}' data-total='{total if total is not None else -1}' "
            f"data-rated='{0 if total is None else 1}'>"
            "<div class='an-l'>"
            f"<div class='an-co mono'>{E(j.get('company',''))}　·　{E(j.get('location',''))}</div>"
            f"<h3>{job_link(j)}</h3>"
            f"{blocker}"
            f"<div class='an-m'>評分 <b>{e.get('score',0)}</b></div>"
            f"<div>{''.join(f'<span class=tok>{E(k)}</span>' for k in all_kw[:6])}</div>"
            f"{jd_html}"
            "<div class='an-act'>"
            f"<button class='btn btn-p act-apply' data-id='{jid}'>開始投遞 →</button>"
            f"<button class='btn btn-g act-unsave' data-id='{jid}'>移出分析</button>"
            + (f"<span class='badge b-n'>已備妥：{'、'.join(done)}</span>" if done else "")
            + "</div></div>"
            f"<div class='an-r'>{score_block}{bars}</div>"
            "</article>"
        )

    content = (
        "<div class='head'><div class='kicker'>第二步 · 判斷</div>"
        "<h1>契合度診斷</h1>"
        "<p>只有你儲存的職缺會出現在這裡。契合度診斷要讀完整 JD，"
        f"所以是你指定才跑。目前的投遞門檻是 {threshold} 分（滿分 13）。</p></div>"
        "<div class='metrics'>"
        + metric("待分析", str(len(saved)), "已儲存、還沒投遞")
        + metric("已診斷", str(len(rated)), f"還有 {len(saved)-len(rated)} 筆沒做")
        + metric("建議投遞", str(len(go)), f"總分 ≥ {threshold+1}")
        + metric("踩到硬門檻", str(sum(1 for r in rated if r['fit'].get('hard_blocker'))),
                 "再怎麼改履歷也過不了")
        + "</div>"
        "<div class='bar'>"
        "<label>搜尋 <input type='search' id='q' placeholder='職缺／公司'></label>"
        "<label><input type='checkbox' id='funrated'> 只看還沒診斷的</label>"
        f"<button class='lnk' data-open='outDlg'>已移出 <b>{len(removed)}</b> 筆</button>"
        "<span class='sp' id='cnt'></span></div>"
        + ("<div class='ancol'>" + "\n".join(cards) + "</div>" if saved else empty(
            "還沒有要診斷的職缺",
            "去<a href='inbox.html'>職缺收件匣</a>把想投的按「☆」，它們就會出現在這裡。"))
        + dialog("outDlg", "已移出", "從契合度診斷移出去的職缺。診斷結果會留著，"
                 "放回來就看得到。", removed, "saved", "放回診斷")
    )

    js = """
    var cards=[].slice.call(document.querySelectorAll('.an'));
    var q=document.getElementById('q'),fu=document.getElementById('funrated'),
        cnt=document.getElementById('cnt');
    function apply(){
      var t=(q?q.value:'').trim().toLowerCase(),n=0;
      cards.forEach(function(c){
        var ok = c.dataset.gone!=='1';
        if(ok&&fu&&fu.checked&&c.dataset.rated==='1') ok=false;
        if(ok&&t&&c.innerText.toLowerCase().indexOf(t)===-1) ok=false;
        c.style.display=ok?'':'none'; if(ok)n++;
      });
      if(cnt) cnt.textContent='顯示 '+n+' 筆';
    }
    if(q) q.addEventListener('input',apply);
    if(fu) fu.addEventListener('change',apply);
    document.querySelectorAll('.act-apply').forEach(function(btn){
      btn.onclick=function(){
        NR.patch(btn.dataset.id,'status','applied',btn,function(){
          btn.closest('.an').dataset.gone='1'; apply();
        });
      };
    });
    document.querySelectorAll('.act-unsave').forEach(function(btn){
      btn.onclick=function(){
        NR.patch(btn.dataset.id,'saved',false,btn,function(){
          btn.closest('.an').dataset.gone='1'; apply();
        });
      };
    });
    NR.dialogs(); apply();
    """
    doc = ui.page("契合度診斷 · NextRole", "analysis", cnt, content, js)
    return _write(path, doc)


# ── ③ 投遞追蹤 ──────────────────────────────────────────────
def render_tracker(b: dict, cfg: dict, path: str) -> str:
    cnt = bd.counts(b)
    tracked = bd.in_stage(b, "tracker")
    tracked.sort(key=lambda kv: kv[1].get("applied_at") or "", reverse=True)
    fn = bd.funnel(b)

    offers = cnt["offer"]
    active = cnt["applied"] + cnt["first"] + cnt["second"] + cnt["third"]
    itv = sum(1 for _, r in tracked if r["status"] in ("first", "second", "third", "offer"))
    rate = f"{100*itv/len(tracked):.0f}%" if tracked else "—"

    steps = "".join(
        f"<div class='step{' last' if s['key']=='offer' else ''}'>"
        f"<div class='sl'>{s['label']}</div><div class='sn'>{s['n']}</div>"
        f"<div class='sp2'>{s['pct']}%</div></div>"
        for s in fn
    )

    body = []
    for jid, rec in tracked:
        j = rec["job"]
        fit = rec.get("fit") or {}
        st = rec["status"]
        sel = "".join(
            f"<option value='{k}'{' selected' if k == st else ''}>{bd.STATUS_ZH[k]}</option>"
            for k in bd.STATUSES
        )
        vc = verdict_class(rec, cfg["fit_threshold"])
        applied = (rec.get("applied_at") or "")[:10]
        body.append(
            f"<tr class='row{' dim' if st in bd.ENDED else ''}' data-id='{jid}' "
            f"data-status='{st}' data-applied='{applied}' "
            f"data-title='{E(j.get('title',''))}' data-company='{E(j.get('company',''))}' "
            f"data-hay='{E((j.get('title','')+' '+j.get('company','')).lower())}'>"
            f"<td><select class='st' data-id='{jid}'>{sel}</select></td>"
            f"<td class='ttl' title='{E(j.get('title',''))}'>{job_link(j)}</td>"
            f"<td class='co'>{E(j.get('company',''))}</td>"
            f"<td class='num'>" + (f"<span class='badge b-{vc}'>{fit['total']}</span>"
                                   if fit.get("total") is not None else
                                   "<span class='meta'>—</span>") + "</td>"
            f"<td><input type='date' class='dt' data-id='{jid}' value='{E(applied)}'></td>"
            f"<td><textarea class='nt' data-id='{jid}' placeholder='備註'>"
            f"{E(rec.get('notes',''))}</textarea></td></tr>"
        )

    table = (
        "<div class='tw'><table id='t'><colgroup>"
        "<col style='width:104px'><col><col style='width:140px'><col style='width:84px'>"
        "<col style='width:142px'><col style='width:250px'>"
        "</colgroup><thead><tr>"
        "<th class='nosort'>狀態</th>"
        "<th data-k='title'>職缺<span class='ind'></span></th>"
        "<th data-k='company'>公司<span class='ind'></span></th>"
        "<th class='nosort rt'>契合度</th>"
        "<th data-k='applied'>投遞日<span class='ind'></span></th>"
        "<th class='nosort'>備註</th>"
        "</tr></thead><tbody>" + "\n".join(body) + "</tbody></table></div>"
    ) if tracked else empty(
        "還沒有投遞紀錄",
        "去<a href='analysis.html'>適合度分析</a>把決定要投的按「開始投遞」，它們就會出現在這裡。")

    content = (
        "<div class='head'><div class='kicker'>第三步 · 追蹤</div>"
        "<h1>投遞追蹤</h1>"
        "<p>真的投出去的職缺才會在這裡。狀態改了會即時存回本機。</p></div>"
        "<div class='metrics'>"
        + metric("總投遞", str(len(tracked)), "累計")
        + metric("進行中", str(active), "尚未收到結果")
        + metric("進到面試", rate, f"{itv} 家")
        + metric("Offer", str(offers), "恭喜" if offers else "還在路上")
        + "</div>"
        + (f"<div class='card pad' style='margin-bottom:18px'>"
           f"<h2>應徵管道漏斗<span class='sp'>感謝信與無聲卡不知道是在哪一關掉的，只計入「已投遞」</span></h2>"
           f"<div class='funnel'>{steps}</div></div>" if tracked else "")
        + "<div class='bar'>"
        "<label>搜尋 <input type='search' id='q' placeholder='職缺／公司'></label>"
        "<label>狀態 <select id='fst'><option value=''>全部</option>"
        + "".join(f"<option value='{k}'>{bd.STATUS_ZH[k]}</option>" for k in bd.STATUSES)
        + "</select></label><span class='sp' id='cnt'></span></div>"
        + table
    )

    js = """
    var rows=[].slice.call(document.querySelectorAll('tr.row'));
    var q=document.getElementById('q'),fst=document.getElementById('fst'),
        cnt=document.getElementById('cnt');
    function apply(){
      var t=(q?q.value:'').trim().toLowerCase(),s=fst?fst.value:'',n=0;
      rows.forEach(function(r){
        var ok=true;
        if(s&&r.dataset.status!==s) ok=false;
        if(ok&&t&&r.dataset.hay.indexOf(t)===-1) ok=false;
        r.style.display=ok?'':'none'; if(ok)n++;
      });
      if(cnt) cnt.textContent='顯示 '+n+' / '+rows.length+' 筆';
    }
    if(q) q.addEventListener('input',apply);
    if(fst) fst.addEventListener('change',apply);
    document.querySelectorAll('select.st').forEach(function(s){
      s.onchange=function(){
        var r=s.closest('tr');
        NR.patch(s.dataset.id,'status',s.value,s,function(){
          r.dataset.status=s.value;
          r.classList.toggle('dim', s.value==='thanks'||s.value==='ghosted');
          apply();
        });
      };
    });
    document.querySelectorAll('textarea.nt').forEach(function(t){
      t.onchange=function(){ NR.patch(t.dataset.id,'notes',t.value,t); };
    });
    document.querySelectorAll('input.dt').forEach(function(d){
      d.onchange=function(){
        var r=d.closest('tr');
        NR.patch(d.dataset.id,'applied_at',d.value,d,function(){
          r.dataset.applied=d.value;
        });
      };
    });
    NR.sortable('t',rows); NR.dialogs(); apply();
    """
    doc = ui.page("投遞追蹤 · NextRole", "tracker", cnt, content, js)
    return _write(path, doc)


def _write(path: str, doc: str) -> str:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(doc)
    return path


def render_all(b: dict | None = None, cfg: dict | None = None) -> list[str]:
    b = b if b is not None else bd.load()
    cfg = cfg if cfg is not None else store.load_config()
    return [
        render_inbox(b, cfg, os.path.join(store.OUTPUT, "inbox.html")),
        render_analysis(b, cfg, os.path.join(store.OUTPUT, "analysis.html")),
        render_tracker(b, cfg, os.path.join(store.OUTPUT, "tracker.html")),
    ]


def main():
    b = bd.load()
    render_all(b)
    c = bd.counts(b)
    print(f"三頁已產生於 {store.OUTPUT}")
    print(f"  收件匣 {c['inbox']} 筆　分析 {c['saved']} 筆　投遞追蹤 {c['tracker']} 筆")
    print("用 `uv run serve.py` 開，不要用 file:// — 連結會空白、改動也存不回去。")


if __name__ == "__main__":
    main()

import {api,empty,badge} from '/base.js'
import {endpoint,heading,init,picker} from './ui.js'
import {deviation} from './scale.js'
import {phase} from './phrases.js'

export async function drift(root,user,selected){
  const {rows,code}=await init(selected)
  if(!code){root.innerHTML=empty('暂无巡测。');return}
  const {report,signed}=await api(endpoint+'/tours/'+code+'/drift')
  const axis=Math.max(1,...Object.values(report.segments).flatMap(row=>row.values.map(Math.abs)))
  const candidate=report.borrow_candidate??report.borrow?.candidate
  const borrowed=report.segments?.night?.borrowed_from??signed?.borrowed_from
  const pending=signed?.review_pending||signed?.status==='pending_review'
  root.innerHTML=heading('昼夜漂移谱','每个授时源先计算中位数，再对来源中位数取中位数；可避免记录较多的时间源支配汇总。')
    +`<div class="clock-layout"><section>${borrowed?`<p class="borrow-line" data-borrowed-from="${borrowed}">夜段实测修正借自复盘 <strong>${borrowed}</strong>，页面与归档回执均已注明。</p>`:''}
      ${pending?'<p class="review-warning" role="status">借用来源已作废，原数保留，本复盘标为待复核。</p>':''}
      ${Object.entries(report.segments).map(([key,row])=>deviation(key,row,axis)).join('')}</section>
    <aside>${picker(rows,code)}<h2>共同校验</h2>${badge(phase[report.phase]??report.phase,report.phase)}<p>各来源中位偏移极差须不超过 ${report.max_range_ms} ms。</p>
    ${candidate&&!signed?`<p class="borrow-hint">夜段样本不足时，可在“复盘签发”借用同亭较早巡次最近一份有效夜段实测：<strong>${candidate.tour??candidate.code}</strong>。</p>`:''}
    </aside></div>`
  root.querySelector('#tour').onchange=e=>drift(root,user,e.target.value)
}

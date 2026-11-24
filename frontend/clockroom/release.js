import {api,empty,h} from '/base.js'
import {action,endpoint,heading,init,picker} from './ui.js'
import {docket,borrowPicker} from './release-sheet.js'

export async function release(root,user,selected){
  const {rows,code}=await init(selected)
  if(!code){root.innerHTML=empty('暂无巡测。');return}
  const path=endpoint+'/tours/'+code
  const {report,signed}=await api(path+'/drift')
  // live 回执在 worker 尚未产出时也会按当前事实即时计算，不阻塞首屏。
  let receipt=null
  if(signed){
    try{receipt=await api(path+'/receipt')}catch{receipt=null}
  }
  const candidates=report.borrow_candidates??report.borrow?.candidates??[]
  const canIssue=user.role==='reviewer'&&!signed
  const voided=Boolean(signed?.voided||signed?.status==='voided')
  const canVoid=user.role==='reviewer'&&signed&&!voided
  // 在借用单上点“作废”，作废的是它借用的来源复盘；在来源单上则作废本单。
  const voidTarget=signed?.borrowed_from||code
  root.innerHTML=heading('复盘签发','确认昼段、夜段校时意见；夜段漏抄时借用同亭较早巡次的有效实测修正，页面与归档回执都注明借自哪次复盘。')
    +`<div class="clock-layout"><section>${docket(report,signed,receipt)}</section><aside>${picker(rows,code)}
    ${canIssue?`<form id="issue-sheet">${borrowPicker(candidates)}
      <details class="manual-fallback"><summary>无来源可借时，直接留夜段校时意见</summary>
        <label>夜段修正 ms（偏移相反数）<input name="night_adjust_ms" type="number" step="0.5" placeholder="例如 -335"></label>
      </details>
      <button>签发校时单</button><p role="status"></p></form>`:''}
    ${canVoid?`<form id="void-sheet"><label>作废登记<input name="reason" maxlength="240" placeholder="作废原因（选填）"></label>
       <small>${signed?.borrowed_from?`此操作将作废借用来源复盘 ${signed.borrowed_from}，本单保留原数并转待复核`:'此操作将作废本复盘；已借用它的校时单转待复核'}</small>
       <button class="danger" type="submit" data-void-target="${h(voidTarget)}">作废</button><p role="status"></p></form>`:''}
    ${voided?'<p class="review-warning">该复盘已作废（重试不会重复登记）。</p>':''}
    </aside></div>`
  root.querySelector('#tour').onchange=e=>release(root,user,e.target.value)
  action(root.querySelector('#issue-sheet'),data=>{
    const body={}
    if(data.source)body.source=data.source
    if(data.night_adjust_ms!==''&&data.night_adjust_ms!=null)
      body.night_adjust_ms=Number(data.night_adjust_ms)
    return api(path+'/issue','POST',body)
  },()=>release(root,user,code))
  action(root.querySelector('#void-sheet'),
    data=>api(endpoint+'/tours/'+voidTarget+'/void','POST',{reason:data.reason||null}),
    ()=>release(root,user,code))
}

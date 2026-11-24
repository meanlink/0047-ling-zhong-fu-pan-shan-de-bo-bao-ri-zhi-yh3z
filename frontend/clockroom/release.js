import {api,empty} from '/base.js'
import {action,endpoint,heading,init,picker} from './ui.js'
import {docket} from './release-sheet.js'

export async function release(root,user,selected){
  const {rows,code}=await init(selected)
  if(!code){root.innerHTML=empty('暂无巡测。');return}
  const path=endpoint+'/tours/'+code
  const {report,signed}=await api(path+'/drift')
  root.innerHTML=heading('复盘签发','确认昼段、夜段校时意见，冻结日志分类和签注，并生成归档回执。')
    +`<div class="clock-layout"><section>${docket(report,signed)}</section><aside>${picker(rows,code)}
    ${user.role==='reviewer'&&!signed?'<form><button>签发校时单</button><p role="status"></p></form>':''}</aside></div>`
  root.querySelector('#tour').onchange=e=>release(root,user,e.target.value)
  action(root.querySelector('form'),()=>api(path+'/issue','POST',{}),()=>release(root,user,code))
}

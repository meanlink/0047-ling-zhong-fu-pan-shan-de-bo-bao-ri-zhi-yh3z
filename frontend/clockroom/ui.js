import {api,h,notice} from '/base.js'
export const endpoint='/api/beacon'
export const heading=(name,about)=>`<header class="clock-head"><h1>${h(name)}</h1><p>${h(about)}</p></header>`
export const options=(rows,display,selected)=>rows.map(row=>`<option value="${h(row.code)}" ${row.code===selected?'selected':''}>${h(display(row))}</option>`).join('')
export const picker=(rows,selected)=>`<label>巡测日<select id="tour">${options(rows,row=>row.name+' / '+row.tour_day,selected)}</select></label>`
export async function init(selected){
  const rows=await api(endpoint+'/tours')
  return {rows,code:selected??rows[0]?.code}
}
export function action(form,send,reload){
  if(!form)return
  form.onsubmit=async event=>{
    event.preventDefault()
    const button=event.submitter
    button.disabled=true
    try{await send(Object.fromEntries(new FormData(form)));await reload()}
    catch(error){notice(form.querySelector('[role=status]'),error.message,true)}
    finally{button.disabled=false}
  }
}

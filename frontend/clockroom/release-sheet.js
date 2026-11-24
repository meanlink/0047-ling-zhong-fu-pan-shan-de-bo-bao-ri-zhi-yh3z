import {h,badge} from '/base.js'
import {ms,phase,segments,sheetStatus} from './phrases.js'

const aliasSource = row => row?.borrowed_from ?? row?.borrow_from ?? row?.source_tour
  ?? row?.source_code ?? row?.from_tour ?? row?.origin_tour ?? row?.source ?? null

export function borrowSource(report,signed){
  return aliasSource(report?.segments?.night) ?? aliasSource(report)
    ?? aliasSource(signed) ?? signed?.borrowed_from ?? null
}

function segmentRow(key,row){
  const from=aliasSource(row)
  const manual=row?.manual
  const tag=from
    ? `<small class="borrow-tag" data-borrowed-from="${h(from)}">夜段实测修正借自复盘 <strong>${h(from)}</strong></small>`
    : manual ? '<small class="manual-tag">志愿站人工校时意见</small>' : ''
  return `<div data-segment="${h(key)}"><dt>${segments[key]??key}建议偏移</dt>
   <dd>${h(ms(row.adjust_ms))}${tag}</dd></div>`
}

function receiptBlock(receipt){
  if(!receipt)return ''
  const night=receipt.clock_adjust_ms?.night
  const from=receipt.borrowed_from ?? aliasSource(receipt)
  const pending=receipt.review_pending||receipt.pending_review||receipt.status==='pending_review'
  return `<section class="archived-receipt" data-receipt data-job-status="${h(receipt.job_status??'')}">
    <h3>归档回执</h3>
    <p>昼段 ${h(ms(receipt.clock_adjust_ms?.sun))} ｜ 夜段 ${h(ms(night))}</p>
    <p data-receipt-borrow="${h(from??'')}">${from?`本回执夜段修正借自复盘 <strong>${h(from)}</strong>`:'本回执来自本次实测'}</p>
    <p>${pending?badge('待复核','pending_review'):badge('回执有效','done')}
       <small>后台任务 ${h(receipt.job_status??receipt.status??'')}</small></p>
  </section>`
}

export function borrowPicker(candidates){
  if(!candidates?.length)return ''
  return `<label>借用夜段实测来源
    <select name="source">
      <option value="">自动借最近一份有效复盘</option>
      ${candidates.map(c=>`<option value="${h(c.tour??c.code)}">${h(c.tour??c.code)} · 夜段 ${h(ms(c.adjust_ms))}</option>`).join('')}
    </select></label>
    <p class="borrow-hint">仅借用同亭较早巡次里最近一份未作废的夜段实测修正，签发后页面与归档回执都会记下借自哪次复盘。</p>`
}

export function docket(report,signed,receipt){
  const code=borrowSource(report,signed)
  const status=signed?.status??signed?.state
  const pending=Boolean(signed?.review_pending||signed?.pending_review||signed?.needs_review
    ||status==='pending_review'||status==='review_pending'||receipt?.review_pending)
  const voided=Boolean(signed?.voided||signed?.is_voided||signed?.revoked||status==='voided')
  const statusChip=voided?badge('已作废','voided revoked')
    :pending?badge('待复核','pending_review review_pending')
    :signed?badge(sheetStatus[status]??'已签发',status||'issued'):''
  const pendingClasses=pending?'is-pending pending_review review_pending':''
  const phaseLabel=phase[report.phase]??report.phase
  return `<article class="docket ${pendingClasses} ${voided?'is-voided voided':''}"
      data-borrowed-from="${h(code??'')}" data-sheet-status="${h(status??'')}"
      data-status="${h(status??'')}" data-pending-review="${pending}" data-review-pending="${pending}"
      data-voided="${voided}">
   <header><h2>复盘校时意见</h2>${badge(phaseLabel,report.phase)}${signed?statusChip:''}</header>
   ${pending?'<p class="review-warning" role="status">来源复盘已作废：已借用的原修正数保留，本单标为<strong>待复核</strong>。</p>':''}
   ${voided?'<p class="review-warning" role="status">本源已作废；已借用它的校时单保留原数并转为<strong>待复核</strong>，作废重试不会重复登记。</p>':''}
   <dl>${Object.entries(report.segments??{}).map(([key,row])=>segmentRow(key,row)).join('')}</dl>
   ${code?`<p class="borrow-line">夜段实测修正借自哪次复盘：<strong data-borrow-source>${h(code)}</strong></p>`:''}
   <p>签注保留排除项 ${h((report.excluded??[]).join('、')||'无')}</p>
   ${signed?`<p>签发人 ${h(signed.editor)}${signed.voided_by?` ｜ 作废登记 ${h(signed.voided_by)}`:''}</p>`:''}
   ${receiptBlock(receipt)}
  </article>`
}

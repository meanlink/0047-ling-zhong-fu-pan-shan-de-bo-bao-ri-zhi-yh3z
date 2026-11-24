export const labels={unstable:'时间源不稳',human:'人工录时误差'}
export const phase={ready:'可签发',disagree:'两源待核对',sparse:'证据不足',borrowed:'夜段借用旧复盘',manual:'夜段人工意见'}
export const segments={sun:'日段',night:'夜段'}
export const sheetStatus={issued:'已签发',pending_review:'待复核',review_pending:'待复核',voided:'已作废',current:'已签发'}
export const ms=value=>value===null||value===undefined?'—':value+' ms'
const formatter=new Intl.DateTimeFormat('zh-CN',{timeZone:'Asia/Shanghai',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',second:'2-digit',hourCycle:'h23'})
export const stamp=moment=>formatter.format(new Date(moment))

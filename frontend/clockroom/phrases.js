export const labels={unstable:'时间源不稳',human:'人工录时误差'}
export const phase={ready:'可签发',disagree:'两源待核对',sparse:'证据不足'}
export const segments={sun:'日段',night:'夜段'}
export const ms=value=>value===null?'—':value+' ms'
const formatter=new Intl.DateTimeFormat('zh-CN',{timeZone:'Asia/Shanghai',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',second:'2-digit',hourCycle:'h23'})
export const stamp=moment=>formatter.format(new Date(moment))

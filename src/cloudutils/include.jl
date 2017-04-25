module CloudUtils

export AWSQueue

export sendmsg, pullmsg, delmsg
export purgequeue

include("msgqueues.jl"); using .MsgQueues
include("awsqueue.jl"); using .AWSQueues
include("utils.jl"); using .Utils

end #module CloudUtils

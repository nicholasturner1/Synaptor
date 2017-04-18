module MsgQueues

export MsgQueue
export sendmsg, pullmsg, delmsg
export purgequeue

abstract MsgQueue


function sendmsg(mq::MsgQueue, msg)
  error("sendmsg not implemented for MsgQueue type $(typeof(mq))")
end


function pullmsg(mq::MsgQueue)
  error("pullmsg not implemented for MsgQueue type $(typeof(mq))")
end


function delmsg(mq::MsgQueue)
  error("delmsg not implemented for MsgQueue type $(typeof(mq))")
end


function purgequeue(mq::MsgQueue)
  error("purgequeue not implemented for MsgQueue type $(typeof(mq))")
end


function Base.length(mq::MsgQueue)
  error("length not implemented for MsgQueue type $(typeof(mq))")
end


end #module MsgQueue

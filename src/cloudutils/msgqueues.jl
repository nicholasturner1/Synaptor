module MsgQueues

export MsgQueue
export sendmsg, pullmsg, delmsg

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

end #module MsgQueue

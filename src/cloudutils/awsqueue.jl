module AWSQueues


using ..MsgQueues
using AWS, AWS.SQS


export AWSQueue


type AWSQueue <: MsgQueue

  env::AWS.AWSEnv
  qurl::String
  receipthandles::Vector{String}

  function AWSQueue(qname ;id=AWS.AWS_ID, seckey=AWS.AWS_SECKEY)
    env = AWS.AWSEnv(; id=id, key=seckey);
    qurl = fetch_url(env, qname)
    receipthandles = String[]

    new(env,qurl,receipthandles)
  end
end


function fetch_url(env, qname)

  resp = AWS.SQS.GetQueueUrl(env; queueName=qname)

  if resp.http_code < 299  resp.obj.queueUrl
  else                     error("Request for Queue URL failed")
  end
end


function MsgQueues.sendmsg(mq::AWSQueue, msg)

  resp = AWS.SQS.SendMessage(mq.env; queueUrl=mq.qurl, messageBody=msg)

  if resp.http_code >= 299  error("Request to Send Message Failed")  end

end


function MsgQueues.pullmsg(mq::AWSQueue)

  resp = AWS.SQS.ReceiveMessage(mq.env; queueUrl=mq.qurl)

  if resp.http_code >= 299  error("Request to Receive Message Failed")  end

  push!(mq.receipthandles, resp.obj.messageSet[1].receiptHandle)

  resp.obj.messageSet[1].body
end


function MsgQueues.delmsg(mq::AWSQueue)

  rh = pop!(mq.receipthandles)

  resp = AWS.SQS.DeleteMessage(mq.env; queueUrl=mq.qurl, receiptHandle=rh)

  if resp.http_code >= 299  error("Request to Delete Message Failed")  end

end


function MsgQueues.purgequeue(mq::AWSQueue)

  resp = AWS.SQS.PurgeQueue(mq.env; queueUrl=mq.qurl)

  if resp.http_code >= 299  error("Request to Purge Queue Failed")  end

end


function Base.length(mq::AWSQueue)

  resp = AWS.SQS.GetQueueAttributes(mq.env; queueUrl=mq.qurl,
                                    attributeNameSet=["ApproximateNumberOfMessages"])

  if resp.http_code >= 299  error("Request to determine length failed")  end

  parse( Int, resp.obj.attributeSet[1].value )
end


end #module AWSQueues

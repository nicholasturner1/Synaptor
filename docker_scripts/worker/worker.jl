#!/usr/bin/env julia
module Worker

include("workertasks.jl"); using .WorkerTasks

using Synaptor; S = Synaptor;

using JSON


jobqueue = S.CloudUtils.AWSQueue("synaptor")
donequeue = S.CloudUtils.AWSQueue("synaptor-done")


function main()

  while true

    taskdict = pulltask(jobqueue)

    try
      perform_task(taskdict)

      update_queues(jobqueue, donequeue, taskdict)
    catch err
      println(err)
      println("Caught error within task. Retrying...")


      try
        perform_task(taskdict)
        update_queues(jobqueue, donequeue, taskdict)
      catch err
        print("ERROR: ")
        println(err)
        println("Giving up on task...")
        println(taskdict)
      end


    end

  end

end


function pulltask(q, sleep_time=5)

  taskdict = Dict();
  while true

    println("Checking for task...")

    try
      if length(q) > 0
        taskdict = JSON.parse(S.CloudUtils.pullmsg(q))
        break
      end
    end

    sleep(sleep_time)

  end

  taskdict
end


function perform_task(taskdict)

  taskname = taskdict["task"]

  @time if taskname == "make semantic map"       semantic_map(taskdict)
  elseif taskname == "convert semmap"            convert_semmap(taskdict)
  elseif taskname == "make expanded maps"        expand_semmaps(taskdict)
  elseif taskname == "perform edge finding"      find_edges(taskdict)
  elseif taskname == "consolidate edge ids"      consolidateids(taskdict)
  elseif taskname == "consolidate continuations" conscontinuations(taskdict)
  elseif taskname == "consolidate duplicates"    consolidatedups(taskdict)
  elseif taskname == "remap segments"            relabel_seg(taskdict)
  elseif taskname == "full EF"                   full_find_edges(taskdict)
  else   warn("unknown task name - skipping...")
  end

end


function update_queues(jobqueue, donequeue, taskdict)

  #removing the last message pulled from the queue
  S.CloudUtils.delmsg(jobqueue)
  #popping it onto the done queue
  S.CloudUtils.sendmsg(donequeue, JSON.json(taskdict))

end

main()

end#module Worker

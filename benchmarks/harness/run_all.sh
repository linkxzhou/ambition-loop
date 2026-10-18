#!/bin/bash
# run everything in background under caffeinate; logs in ~/skev/ambition-loop/logs
cd ~/skev/ambition-loop && mkdir -p logs ~/skev-base
export PAR=${PAR:-4}
( python3 mac_run.py ambition-loop    > logs/run-en.log 2>&1
  python3 mac_grade.py ambition-loop  > logs/grade-en.log 2>&1 ) &
( python3 mac_run.py ambition-loop-zh > logs/run-zh.log 2>&1
  python3 mac_grade.py ambition-loop-zh > logs/grade-zh.log 2>&1 ) &
wait
( PAR=4 python3 mac_trigger.py ambition-loop > logs/trigger-en.log 2>&1 ) &
( PAR=4 python3 mac_trigger.py ambition-loop-zh > logs/trigger-zh.log 2>&1 ) &
wait
echo ALLDONE > logs/ALLDONE

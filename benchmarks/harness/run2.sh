#!/bin/bash
cd ~/skev/ambition-loop
# 1) regrade iteration-1 with the improved grader (before baselines get rerun in ~/skev-base)
REGRADE=1 PAR=4 python3 mac_grade.py ambition-loop    > logs/regrade1-en.log 2>&1 &
REGRADE=1 PAR=4 python3 mac_grade.py ambition-loop-zh > logs/regrade1-zh.log 2>&1 &
wait
# 2) iteration-2 with skill v1.0.1 (with_skill all; without_skill only missing/glitched)
( ITER=iteration-2 PAR=3 python3 mac_run.py ambition-loop    > logs/run2-en.log 2>&1; ITER=iteration-2 PAR=4 python3 mac_grade.py ambition-loop    > logs/grade2-en.log 2>&1 ) &
( ITER=iteration-2 PAR=3 python3 mac_run.py ambition-loop-zh > logs/run2-zh.log 2>&1; ITER=iteration-2 PAR=4 python3 mac_grade.py ambition-loop-zh > logs/grade2-zh.log 2>&1 ) &
wait
PAR=4 python3 mac_trigger.py ambition-loop > logs/trigger2-en.log 2>&1 &
PAR=4 python3 mac_trigger.py ambition-loop-zh > logs/trigger2-zh.log 2>&1 &
wait
echo DONE2 > logs/DONE2

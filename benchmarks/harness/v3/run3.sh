#!/bin/bash
cd ~/skev/ambition-loop
mkdir -p logs3
for SK in ambition-loop ambition-loop-zh; do
  L=$([ $SK = ambition-loop ] && echo en || echo zh)
  ( RUN=1 PAR=3 python3 mac_run3.py $SK > logs3/run1-$L.log 2>&1
    RUN=2 PAR=3 python3 mac_run3.py $SK 1 3 7 > logs3/run2-$L.log 2>&1
    PAR=4 python3 mac_grade3.py $SK > logs3/grade-$L.log 2>&1
    PAR=4 python3 mac_trigger3.py $SK > logs3/trigger-$L.log 2>&1 ) &
done
wait
echo DONE3 > logs3/DONE3

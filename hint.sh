#!/bin/bash
SLEEP_SEC=1.4
sleep $SLEEP_SEC
while ! curl -s -o /dev/null http://127.0.0.1:8081
do 
    echo -n "not ready, waiting for $SLEEP_SEC seconds." $'\r'
    sleep 0.2; 
    SLEEP_SEC=$(echo $SLEEP_SEC + 0.2 | bc)
done
echo ""
echo "open $(gp url 8081)/test/#/frontend to test nonebot!"; 


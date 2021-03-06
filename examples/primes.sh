#!/bin/bash
function is_prime() {
    n=$1
    if [ "${n}" -lt 2 ]; then return; fi
    if [ "$((n % 2))" -eq 0 ]; then
        if [ "${n}" == "2" ]; then echo "yes"; fi
        return;
    fi
    d=$(echo "sqrt(${n})"|bc)
    for k in $(seq 3 2 ${d}); do
        if [ "$((n % k))" -eq 0 ]; then return; fi
    done
    echo "yes"
}

for n in $(seq 0 $1); do
    if [ "$(is_prime ${n})" == "yes" ]; then
        echo -n "${n} ";
    fi
done
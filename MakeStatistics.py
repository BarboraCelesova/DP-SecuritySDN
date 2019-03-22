#!/usr/bin/python

# Sript to count statistics from file (output from Specter.py)

from collections import Counter

def main():
    f = open("/home/barbora/PycharmProjects/DP-SecuritySDN/a.txt", "r")
    lineList = []

    for line in f:
        lineList.append(line)

    all_states = {}
    for i in range(0, len(lineList)):
        line = lineList[i].split(" ")
        state = line[1]
        line = lineList[i].split("--")
        args = line[2].split(" ")
        ip_add = args[2]


        if state not in all_states:
            all_states[state] = [ip_add]
        else:
            all_states[state].append(ip_add)

    for i in all_states:
        print len(all_states[i])


main()

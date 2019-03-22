#!/usr/bin/python

# Sript to count number of flooded packets

from collections import Counter

def main():
    f = open("/home/barbora/PycharmProjects/DP-SecuritySDN/a.txt", "r")
    lineList = []
    for line in f:
        lineList.append(line)

    times = []
    for i in range(0, len(lineList)):
        tajm = lineList[i].split(" ")
        x = tajm[0].split(".")
        times.append(x[0])

    counter = sorted(Counter(times).items())
    numline = 1
    shouldBe = 150

    for i in counter:
        print numline, i, shouldBe
        numline += 1
        shouldBe += 2

main()

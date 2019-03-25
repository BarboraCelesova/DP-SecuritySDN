    startTime = datetime.datetime.utcnow()
    sleeptime = 1 - (startTime.microsecond / 1000000.0)
    time.sleep(sleeptime)

    #NoNattack traffic
    for i in [2,3,4,6,7,9,10,12,13,14]:
        for j in range(1,6):
            host[i].cmd('iperf -c 10.0.0.10' + str(j) + ' -u -t 60 &')
            # host[i].cmd('hping3 -D -c 50 -i 1 -2 10.0.0.10' + str(j) + ' &')

    #Attack traffic
    for i in [1,5,8,11,15]:
        for j in range(1, 6):
            host[i].cmd('iperf -c 10.0.0.10' + str(j) + ' -u -t 60 &')
            # host[i].cmd('hping3 -D -c 50 -i 1 -2 10.0.0.10' + str(j) + ' &> h' + str(i) + '.txt &')

    timer = 59

    t = datetime.datetime.utcnow()
    sleeptime = 1 - (t.microsecond / 1000000.0)
    time.sleep(sleeptime)

    # time.sleep(1)
    for j in range(106,115):
        for i in [1,5,8,11,15]:
            host[i].cmd('iperf -c 10.0.0.' + str(j) + ' -u -t ' + str(timer) + ' &')
            # host[i].cmd('hping3 -D -c ' + str(timer) + ' -i 1 -2 10.0.0.' + str(j) + ' &> h' + str(i) + '.txt &')
            timer -= 1
            t = datetime.datetime.utcnow()
            sleeptime = 1 - (t.microsecond / 1000000.0)
            time.sleep(sleeptime)

    stopTime = datetime.datetime.utcnow()
    diff = stopTime - startTime
    sleeptime = 49 - diff.seconds
    time.sleep(sleeptime)

    for i in range(1, 16):
        host[i].cmd('sudo pkill -9 -f iperf &')



    # for i in [1, 5, 8, 11]:
    #     host[i].cmd('hping3 -c ' + str(timer) + ' -i 1 -2 10.0.0.115 &> h' + str(i) + '.txt &')
    #     timer -= 1
    #     time.sleep(1)

    # ///////////////////////////////////////////////////////////

    # t = datetime.datetime.utcnow()
    # print t
    # print t.second
    # print t.microsecond
    # sleeptime = 1 - (t.microsecond / 1000000.0)
    # print sleeptime
    # time.sleep(sleeptime)
    # host[1].cmd('sudo wireshark &')
    #
    # attackers = [1,5,8,11,15]
    # count = 0
    # for n in range(0, 50):
    #     count = 0
    #     for j in range(0, 5 + (n / 5)):
    #         for i in attackers:
    #             host[i].cmd('hping3 -c 1 -2 10.0.0.' + str(randint(101, 115)) + ' &')
    #             host[i].cmd('hping3 -c 1 -2 10.0.0.' + str(randint(101, 115)) + ' &')
    #             count += 1
    #     for k in range(0, n % 5):
    #         host[attackers[randint(0, len(attackers) - 1)]].cmd('hping3 -c 1 -2 10.0.0.' + str(randint(101, 115)) + ' &')
    #         host[attackers[randint(0, len(attackers) - 1)]].cmd('hping3 -c 1 -2 10.0.0.' + str(randint(101, 115)) + ' &')
    #         count += 1
    #     print t.second, count
    #     t = datetime.datetime.utcnow()
    #     sleeptime = 1 - (t.microsecond / 1000000.0)
    #     time.sleep(sleeptime)

-----------------------------------
#NoNattack traffic
    for i in range(1, 11):
        for j in range(1, 4):
            host[i].cmd('iperf -c 10.0.0.10' + str(j) + ' -u -t 9 &')

    for i in range(11, 16):
        for j in range(1, 5):
            host[i].cmd('iperf -c 10.0.0.10' + str(j) + ' -u -t 9 &')

    # #Attack traffic
    for i in range(80, 85):
        for j in range(1, 6):
            host[i].cmd('iperf -c 10.0.0.10' + str(j) + ' -u -t 60 &')

    #To wait until beginning of another sec
    t = datetime.datetime.utcnow()
    sleeptime = 1 - (t.microsecond / 1000000.0)
    time.sleep(sleeptime)

    for j in range(6, 8):
        for i in range(80, 85):
            host[i].cmd('iperf -c 10.0.0.10' + str(j) + ' -u -t 60 &')
            t = datetime.datetime.utcnow()
            sleeptime = 1 - (t.microsecond / 1000000.0)
            time.sleep(sleeptime)

    for i in range(1, 16):
        host[i].cmd('sudo pkill -9 -f iperf &')

    t = datetime.datetime.utcnow()
    sleeptime = 1 - (t.microsecond / 1000000.0)
    time.sleep(sleeptime)

    #---after first 10 seconds

    # NoNattack traffic
    for i in range(16, 26):
        for j in range(1, 4):
            host[i].cmd('iperf -c 10.0.0.10' + str(j) + ' -u -t 9 &')
    for i in range(27, 32):
        for j in range(1, 5):
            host[i].cmd('iperf -c 10.0.0.10' + str(j) + ' -u -t 9 &')
    #Attack
    for j in range(6, 8):
        for i in range(80, 85):
            host[i].cmd('iperf -c 10.0.0.10' + str(j) + ' -u -t 60 &')
            t = datetime.datetime.utcnow()
            sleeptime = 1 - (t.microsecond / 1000000.0)
            time.sleep(sleeptime)

    for i in range(16, 32):
        host[i].cmd('sudo pkill -9 -f iperf &')

    t = datetime.datetime.utcnow()
    sleeptime = 1 - (t.microsecond / 1000000.0)
    time.sleep(sleeptime)
    # ---after first 20 seconds

    # NoNattack traffic
    for i in range(32, 42):
        for j in range(1, 4):
            host[i].cmd('iperf -c 10.0.0.10' + str(j) + ' -u -t 20 &')
    for i in range(43, 48):
        for j in range(1, 5):
            host[i].cmd('iperf -c 10.0.0.10' + str(j) + ' -u -t 20 &')

    # Attack
    for j in range(6, 8):
        for i in range(80, 85):
            host[i].cmd('iperf -c 10.0.0.10' + str(j) + ' -u -t 60 &')
            t = datetime.datetime.utcnow()
            sleeptime = 1 - (t.microsecond / 1000000.0)
            time.sleep(sleeptime)

    for i in range(32, 48):
        host[i].cmd('sudo pkill -9 -f iperf &')

    # ---after first 30 seconds

    # NoNattack traffic
    for i in range(48, 59):
        for j in range(1, 4):
            host[i].cmd('iperf -c 10.0.0.10' + str(j) + ' -u -t 20 &')
    for i in range(59, 64):
        for j in range(1, 5):
            host[i].cmd('iperf -c 10.0.0.10' + str(j) + ' -u -t 20 &')

    # Attack
    for j in range(6, 8):
        for i in range(80, 85):
            host[i].cmd('iperf -c 10.0.0.10' + str(j) + ' -u -t 60 &')
            t = datetime.datetime.utcnow()
            sleeptime = 1 - (t.microsecond / 1000000.0)
            time.sleep(sleeptime)

    for i in range(48, 64):
        host[i].cmd('sudo pkill -9 -f iperf &')
    for i in range(80, 85):
        host[i].cmd('sudo pkill -9 -f iperf &')

    # ---after first 40 seconds

    # NoNattack traffic
    for i in range(64, 75):
        for j in range(1, 4):
            host[i].cmd('iperf -c 10.0.0.10' + str(j) + ' -u -t 20 &')
    for i in range(75, 80):
        for j in range(1, 5):
            host[i].cmd('iperf -c 10.0.0.10' + str(j) + ' -u -t 20 &')

    # Attack traffic
    for i in range(86, 96):
        for j in range(10, 24):
            host[i].cmd('iperf -c 10.0.0.10' + str(j) + ' -u -t 60 &')

    # To wait until beginning of another sec
    t = datetime.datetime.utcnow()
    sleeptime = 1 - (t.microsecond / 1000000.0)
    time.sleep(sleeptime)


    for i in range(86, 96):
        host[i].cmd('iperf -c 10.0.0.125 -u -t 20 &')
        t = datetime.datetime.utcnow()
        sleeptime = 1 - (t.microsecond / 1000000.0)
        time.sleep(sleeptime)

    for i in range(64, 80):
        host[i].cmd('sudo pkill -9 -f iperf &')
    for i in range(86, 96):
        host[i].cmd('sudo pkill -9 -f iperf &')


# Copyright (C) 2011 Nippon Telegraph and Telephone Corporation.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_4, ofproto_v1_3
from ryu.lib.mac import haddr_to_bin
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import ether_types
from ryu.lib.packet import ipv4
from ryu.lib.packet import arp
from ryu import cfg
from datetime import datetime, date
import time
import thread
import threading

# Global variables
incoming_packetin_list = {}
confidence_list = {}
default_confidence_value = 1
time_slot = 1000
min_confidence_value = (1,)
max_confidence_value = (1,)
number_of_queues = 0
total_buffers_length = 0
priority_buffer = {}
beta = 2
alpha = 0.9
packet_in_counters_list = {}
total_count_per_timeslot = 0
threshold_user = {}
threshold_malicious_user = 0.1
max_threshold = 5
service_rate = 0

sem_incoming_packetin_list = threading.Semaphore()
sem_priority_buffer = threading.Semaphore()
sem_packet_in_counters_list = threading.Semaphore()
sem_total_count_per_timeslot = threading.Semaphore()
sem_threshold_user = threading.Semaphore()
sem_confidence_list = threading.Semaphore()
sem_max_min_confidence_value = threading.Semaphore()


class SimpleSwitch14(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_4.OFP_VERSION]
    # OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        #do not delete or comment this print
        print 'State Time Src_IP'

        global number_of_queues
        global priority_buffer
        global total_buffers_length
        global list_of_priority_users
        global max_threshold

        super(SimpleSwitch14, self).__init__(*args, **kwargs)
        self.mac_to_port = {}

        CONF = cfg.CONF
        CONF.register_opts([
            cfg.IntOpt('NoQueues', default=3),
            cfg.IntOpt('TotalBuffLength', default=10),
            cfg.IntOpt('Threshold', default=5)
        ])

        number_of_queues = CONF.NoQueues
        total_buffers_length = CONF.TotalBuffLength
        max_threshold = CONF.Threshold

        sem_priority_buffer.acquire()
        for i in range(1, number_of_queues + 1):
            priority_buffer[i] = []
        sem_priority_buffer.release()

        try:
            thread.start_new_thread(self.serving_requests)
            thread.start_new_thread(self.time_slot)
        except:
            print "Error: unable to start thread"

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):

        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # install table-miss flow entry
        #
        # We specify NO BUFFER to max_len of the output action due to
        # OVS bug. At this moment, if we specify a lesser number, e.g.,
        # 128, OVS will send Packet-In with invalid buffer_id and
        # truncated packet data. In that case, we cannot output packets
        # correctly.  The bug has been fixed in OVS v2.1.0.
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                          ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions)


    def add_flow(self, datapath, priority, match, actions):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                             actions)]

        mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                match=match, instructions=inst)
        datapath.send_msg(mod)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        global confidence_list
        global incoming_packetin_list

        # Returns a datetime object containing the local date and time
        dateTimeObj = datetime.now()
        # get the time object from datetime object
        timeObj = dateTimeObj.time()
        timeStr = timeObj.strftime("%H:%M:%S.%f")
        msg = ev.msg

        pkt = packet.Packet(msg.data)
        src_ip = self.find_src_ip_add(pkt)

        eth = pkt.get_protocols(ethernet.ethernet)[0]

        if src_ip is None:
            self.create_flow(msg)
            return

        if eth.ethertype == ether_types.ETH_TYPE_LLDP:
            # ignore lldp packet
            return

        # self.logger.info("%s -- packet in %s ... %s %s %s %s", timeStr, src_ip, msg.datapath.id, eth.src, eth.dst, msg.match['in_port'])
        # print timeStr, src_ip, msg.datapath.id, eth.src, eth.dst, msg.match['in_port']
        print 'NEW_PACKET_IN', timeStr, src_ip

        # # process priority users with highest priority
        # for ip in list_of_priority_users:
        #     if src_ip is ip:
        #         self.create_flow(msg)


        # ----Call Spectre Modules--------
        self.confidence_award(ev)
        # ------------

    def create_flow(self, msg):
        global service_rate

        datapath = msg.datapath

        pkt = packet.Packet(msg.data)

        src_ip = self.find_src_ip_add(pkt)

        eth = pkt.get_protocols(ethernet.ethernet)[0]

        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        in_port = msg.match['in_port']

        dst = eth.dst
        src = eth.src

        dpid = datapath.id
        self.mac_to_port.setdefault(dpid, {})

        # learn a mac address to avoid FLOOD next time.
        self.mac_to_port[dpid][src] = in_port

        if dst in self.mac_to_port[dpid]:
            out_port = self.mac_to_port[dpid][dst]
        else:
            out_port = ofproto.OFPP_FLOOD

        actions = [parser.OFPActionOutput(out_port)]

        # install a flow to avoid packet_in next time
        if out_port != ofproto.OFPP_FLOOD:
            match = parser.OFPMatch(in_port=in_port, eth_dst=dst, eth_src=src)
            self.add_flow(datapath, 1, match, actions)

        data = None
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data

        out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                  in_port=in_port, actions=actions, data=data)

        # Returns a datetime object containing the local date and time
        dateTimeObj = datetime.now()
        # get the time object from datetime object
        timeObj = dateTimeObj.time()
        dept_time = timeObj.strftime("%H:%M:%S.%f")

        # # TODO uncomment
        # if service_rate <= 100:
        #     service_rate += 1
        #     if src_ip is not None:
        #         print 'PASSED', dept_time, src_ip
        #
        #     datapath.send_msg(out)
        # else:
        #     print 'REJECTED_SERVICE_RATE_EXCEEDED', dept_time, src_ip

        if src_ip is not None:
            print 'PASSED', dept_time, src_ip

        datapath.send_msg(out)


    def confidence_award(self, ev):
        global confidence_list
        global default_confidence_value
        global incoming_packetin_list
        global total_count_per_timeslot
        global packet_in_counters_list
        global list_of_priority_users

        buffer_capacity = 0
        rejected = 0

        msg = ev.msg
        pkt = packet.Packet(msg.data)
        src_ip = self.find_src_ip_add(pkt)

        if src_ip is None:
            return

        arrival_time = int(round(time.time() * 1000))

        # Returns a datetime object containing the local date and time
        dateTimeObj = datetime.now()
        # get the time object from datetime object
        timeObj = dateTimeObj.time()
        dt_arrival_time = timeObj.strftime("%H:%M:%S.%f")

        self.update_packet_in_counter_list(src_ip)

        # store arrival time and source IP add
        if arrival_time not in incoming_packetin_list:
            sem_incoming_packetin_list.acquire()
            incoming_packetin_list[arrival_time] = [src_ip]
            sem_incoming_packetin_list.release()

        else:
            sem_incoming_packetin_list.acquire()
            incoming_packetin_list[arrival_time].append(src_ip)
            sem_incoming_packetin_list.release()

        if src_ip not in confidence_list:
            confidence_list[src_ip] = default_confidence_value
            self.update_min_max_confidence_value(src_ip, default_confidence_value)

            sem_threshold_user.acquire()
            threshold_user[src_ip] = max_threshold
            sem_threshold_user.release()

        else:
            # self.logger.info('!!!!!THRESHOLD USER', threshold_user)
            # if total request from sender in this time slot is more than threshold for him
            if packet_in_counters_list[src_ip] > threshold_user[src_ip]:
                # give him worse confidence value
                # self.logger.info('REJECTED -- %s, %s, thr %s', src_ip, packet_in_counters_list[src_ip], threshold_user[src_ip])
                sem_confidence_list.acquire()
                confidence_list[src_ip] = alpha * confidence_list[src_ip] - 0.1
                sem_confidence_list.release()
                #reject this request
                print 'REJECTED', dt_arrival_time, src_ip
                rejected = 1
                self.blacklist_user(src_ip, msg, dt_arrival_time)
                self.update_min_max_confidence_value(src_ip, confidence_list[src_ip])
                # break function
                return
            else:
                for i in priority_buffer:
                    buffer_capacity += len(priority_buffer[i])
                buffer_capacity = buffer_capacity/total_buffers_length
                # check if controller is under attack
                if buffer_capacity <= 0.95:
                    sem_confidence_list.acquire()
                    confidence_list[src_ip] = alpha*confidence_list[src_ip] + 0.1
                    sem_confidence_list.release()
                else:
                    sem_confidence_list.acquire()
                    confidence_list[src_ip] = alpha*confidence_list[src_ip] - 0.1
                    sem_confidence_list.release()

            rejected = self.blacklist_user(src_ip, msg, dt_arrival_time)
            self.update_min_max_confidence_value(src_ip, confidence_list[src_ip])

        if rejected == 0:
            self.sorting_to_queues(ev, dt_arrival_time)

    def blacklist_user(self, src_ip, msg, dt_arrival_time):
        global confidence_list
        global threshold_malicious_user

        if confidence_list[src_ip] < threshold_malicious_user:
            print 'REJECTED_blacklisted', dt_arrival_time, src_ip
            # self.logger.info('***BLACKLISTED %s, %s, %s ', dt_arrival_time, src_ip, confidence_list[src_ip])
            datapath = msg.datapath
            ofproto = datapath.ofproto
            parser = datapath.ofproto_parser
            inst = [parser.OFPInstructionActions(ofproto.OFPIT_CLEAR_ACTIONS, [])]
            in_port = msg.match['in_port']
            match = parser.OFPMatch(
                in_port=in_port,
                eth_type=ether_types.ETH_TYPE_IP,
                ipv4_src=src_ip)
            priority = 100
            mod = parser.OFPFlowMod(
                datapath=datapath,
                match=match,
                command=ofproto.OFPFC_ADD,
                priority=priority,
                instructions=inst)
            datapath.send_msg(mod)
            return -1
        return 0

    def sorting_to_queues(self, ev, arrival_time):
        global priority_buffer
        actual_total_buffer_length = 0

        msg = ev.msg
        pkt = packet.Packet(msg.data)
        src_ip = self.find_src_ip_add(pkt)

        if max_confidence_value[0] - min_confidence_value[0] == 0 or confidence_list[src_ip] - min_confidence_value[
            0] == 0:
            index_to_buffer = number_of_queues
        else:
            index_to_buffer = int(round(((float(confidence_list[src_ip]) - float(min_confidence_value[0])) / (
                        float(max_confidence_value[0]) - float(min_confidence_value[0]))) * float(number_of_queues)))
            if index_to_buffer == 0:
                index_to_buffer = 1

        sem_priority_buffer.acquire()
        for i in range(1, number_of_queues + 1):
            actual_total_buffer_length = len(priority_buffer[i])

        if actual_total_buffer_length < total_buffers_length:
            priority_buffer[index_to_buffer].append(msg)
        elif index_to_buffer == 1:
            print 'REJECTED', arrival_time, src_ip
        else:
            for i in range(1, index_to_buffer):
                if len(priority_buffer[i]) > 0:
                    print 'REJECTED_POP', arrival_time, '-'
                    priority_buffer[i].pop()
                    priority_buffer[index_to_buffer].append(msg)
                    sem_priority_buffer.release()
                    return
            print 'REJECTED_NOT_ENOUGH_SPACE', arrival_time, src_ip
        sem_priority_buffer.release()

    def serving_requests(self):
        global number_of_queues
        global priority_buffer
        global beta
        actual_total_buffer_length = 0

        while True:
            actual_buffer_length = [0]
            sem_priority_buffer.acquire()
            for i in range(1, number_of_queues + 1):
                actual_total_buffer_length = len(priority_buffer[i])

            if actual_total_buffer_length != 0:
                weight = [0, ]

                # count weights
                for i in range(1, number_of_queues):
                    weight.append(
                        int(round((len(priority_buffer[i]) / max(len(priority_buffer[1]), 1)) * (beta ** (i - 1)))))

                for i in range(1, number_of_queues + 1):
                    actual_buffer_length.append(len(priority_buffer[i]))
                sem_priority_buffer.release()

                # serve request from the buffer with the highest priority
                buffer_length = actual_buffer_length[number_of_queues]
                if buffer_length != 0:
                    for j in range(0, buffer_length):
                        self.create_flow(priority_buffer[number_of_queues].pop(0))

                # serve stored requests
                for i in range(number_of_queues - 1, 0, -1):
                    if weight[i] < actual_buffer_length[i]:
                        self.logger.info('Actual buffer length, weight %s %s', actual_buffer_length[i], weight[i])
                        for j in range(0, weight[i]):
                            if actual_buffer_length[i] > 0:
                                self.create_flow(priority_buffer[i].pop(0))
                            actual_buffer_length[i] -= 1
                    else:
                        buffer_length = actual_buffer_length[i]
                        for j in range(0, buffer_length - 1):
                            self.create_flow(priority_buffer[i].pop(0))
                time.sleep(0.00001)

            else:
                sem_priority_buffer.release()
                time.sleep(0.00001)

    def find_src_ip_add(self, pkt):
        arp_pkt = pkt.get_protocol(arp.arp)
        ip_pkt = pkt.get_protocol(ipv4.ipv4)

        if arp_pkt:
            arp_src_ip = arp_pkt.src_ip
            return arp_src_ip
        elif ip_pkt:
            ip_src_ip = ip_pkt.src
            return ip_src_ip
        else:
            pass

    def update_min_max_confidence_value(self, src_ip, new_value):
        global min_confidence_value
        global max_confidence_value

        if len(min_confidence_value) == 1 and len(max_confidence_value) == 1:
            sem_max_min_confidence_value.acquire()
            min_confidence_value = (new_value, src_ip)
            max_confidence_value = (new_value, src_ip)
            sem_max_min_confidence_value.release()

        elif min_confidence_value[0] > new_value or min_confidence_value[1] == src_ip:
            sem_max_min_confidence_value.acquire()
            min_confidence_value = (new_value, src_ip)
            sem_max_min_confidence_value.release()

        elif max_confidence_value[0] < new_value or max_confidence_value[1] == src_ip:
            sem_max_min_confidence_value.acquire()
            max_confidence_value = (new_value, src_ip)
            sem_max_min_confidence_value.release()


    def update_packet_in_counter_list(self, src_ip):
        global packet_in_counters_list
        global total_count_per_timeslot

        if src_ip not in packet_in_counters_list:
            sem_packet_in_counters_list.acquire()
            packet_in_counters_list[src_ip] = 1
            sem_packet_in_counters_list.release()
        else:
            sem_packet_in_counters_list.acquire()
            packet_in_counters_list[src_ip] += 1
            sem_packet_in_counters_list.release()

        sem_total_count_per_timeslot.acquire()
        total_count_per_timeslot += 1
        sem_total_count_per_timeslot.release()

    def time_slot(self):
        global packet_in_counters_list
        global total_count_per_timeslot
        global confidence_list
        global service_rate

        number_of_slots = 0
        time.sleep(1)

        while True:
            start = datetime.now()
            service_rate = 0

            old_packet_in_counters_list = packet_in_counters_list

            sem_packet_in_counters_list.acquire()
            packet_in_counters_list = {}
            sem_packet_in_counters_list.release()

            sem_total_count_per_timeslot.acquire()
            total_count_per_timeslot = 0
            sem_total_count_per_timeslot.release()

            for src_ip in confidence_list:
                # Sender did not send any packet in this time slot update his CV
                if src_ip not in old_packet_in_counters_list:
                    # sem_confidence_list.acquire()
                    # confidence_list[src_ip] = alpha * confidence_list[src_ip]
                    # sem_confidence_list.release()
                    pass
                # At the end of each time slot update threshold for user
                else:
                    if (old_packet_in_counters_list[src_ip] <= threshold_user[src_ip]) and (threshold_user[src_ip] < max_threshold):
                        sem_threshold_user.acquire()
                        threshold_user[src_ip] += 1
                        # self.logger.info('++++++++++ THRESHOLD %s %s', src_ip, threshold_user[src_ip])
                        sem_threshold_user.release()
                    elif old_packet_in_counters_list[src_ip] > threshold_user[src_ip] > 0:
                        sem_threshold_user.acquire()
                        threshold_user[src_ip] -= 1
                        # self.logger.info('---------- THRESHOLD %s %s', src_ip, threshold_user[src_ip])
                        sem_threshold_user.release()

            last = datetime.now()
            cakaj = last - start
            seconds = cakaj.total_seconds()
            # self.logger.info('@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@ WORKER PRACOVAL %s', str(seconds))
            if (1 - seconds) > 0:
                time.sleep(1 - seconds)

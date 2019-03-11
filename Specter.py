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
from ryu.ofproto import ofproto_v1_5, ofproto_v1_0
from ryu.lib.mac import haddr_to_bin
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import ether_types
from ryu.lib.packet import ipv4
from ryu.lib.packet import arp
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
number_of_queues = 3
total_buffers_length = 300
priority_buffer = {}
beta = 2
alpha = 0.9
packet_in_counters_list = {}
total_count_per_timeslot = 0
threshold_user = {}
threshold_malicious_user = 0

sem_incoming_packetin_list = threading.Semaphore()
sem_priority_buffer = threading.Semaphore()
sem_packet_in_counters_list = threading.Semaphore()
sem_total_count_per_timeslot = threading.Semaphore()

#TODO 2
sem_threshold_user = threading.Semaphore()
sem_threshold_malicious_user = threading.Semaphore

#TODO apply these semaphores
sem_confidence_list = threading.Semaphore()
#sem_max_min_confidence_value = threading.Semaphore()

# TODO Add option for administrator to set some values (ex. number of queues, total buffers length and so on..)

class SimpleSwitch15(app_manager.RyuApp):
    #OFP_VERSIONS = [ofproto_v1_5.OFP_VERSION]
    OFP_VERSIONS = [ofproto_v1_0.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        global number_of_queues
        global priority_buffer

        super(SimpleSwitch15, self).__init__(*args, **kwargs)
        self.mac_to_port = {}

        sem_priority_buffer.acquire()
        for i in range(1, number_of_queues + 1):
            priority_buffer[i] = []
        sem_priority_buffer.release()

        try:
            thread.start_new_thread(self.serving_requests)
            thread.start_new_thread(self.time_slot)
            #return
        except:
            print "Error: unable to start thread"

    # v 1.5
    # @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    # def switch_features_handler(self, ev):
    #     datapath = ev.msg.datapath
    #     ofproto = datapath.ofproto
    #     parser = datapath.ofproto_parser
    #
    #     # install table-miss flow entry
    #     #
    #     # We specify NO BUFFER to max_len of the output action due to
    #     # OVS bug. At this moment, if we specify a lesser number, e.g.,
    #     # 128, OVS will send Packet-In with invalid buffer_id and
    #     # truncated packet data. In that case, we cannot output packets
    #     # correctly.  The bug has been fixed in OVS v2.1.0.
    #     match = parser.OFPMatch()
    #     actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
    #                                       ofproto.OFPCML_NO_BUFFER)]
    #     self.add_flow(datapath, 0, match, actions)

    # v 1.5
    # def add_flow(self, datapath, priority, match, actions):
    #     ofproto = datapath.ofproto
    #     parser = datapath.ofproto_parser
    #
    #     inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
    #                                          actions)]
    #
    #     mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
    #                             match=match, instructions=inst)
    #     datapath.send_msg(mod)

    #v 1.0
    def add_flow(self, datapath, in_port, dst, src, actions):
        ofproto = datapath.ofproto

        match = datapath.ofproto_parser.OFPMatch(
            in_port=in_port,
            dl_dst=haddr_to_bin(dst), dl_src=haddr_to_bin(src))

        mod = datapath.ofproto_parser.OFPFlowMod(
            datapath=datapath, match=match, cookie=0,
            command=ofproto.OFPFC_ADD, idle_timeout=0, hard_timeout=0,
            priority=ofproto.OFP_DEFAULT_PRIORITY,
            flags=ofproto.OFPFF_SEND_FLOW_REM, actions=actions)
        datapath.send_msg(mod)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        global confidence_list
        global incoming_packetin_list

        msg = ev.msg

        pkt = packet.Packet(msg.data)
        src_ip = self.find_src_ip_add(pkt)

        eth = pkt.get_protocols(ethernet.ethernet)[0]

        if src_ip is None:
            self.create_flow(msg)
            return

        #print pkt

        if eth.ethertype == ether_types.ETH_TYPE_LLDP:
            # ignore lldp packet
            return

        dst = eth.dst
        src = eth.src
        # v 1.5
        #in_port = msg.match['in_port']


        #print " Prisiel packetin "
        # v 1.5
        #self.logger.info("packet in %s ... %s %s %s %s", src_ip, msg.datapath.id, src, dst, in_port)

        # v 1.0
        self.logger.info("packet in %s ... %s %s %s %s", src_ip, msg.datapath.id, src, dst, msg.in_port)

        # ------------
        self.confidence_award(ev)
        # ------------

    def create_flow(self, msg):

        datapath = msg.datapath

        pkt = packet.Packet(msg.data)
        src_ip = self.find_src_ip_add(pkt)
        eth = pkt.get_protocols(ethernet.ethernet)[0]

        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        # v 1.5
        #in_port = msg.match['in_port']

        dst = eth.dst
        src = eth.src

        dpid = datapath.id
        self.mac_to_port.setdefault(dpid, {})

        # v 1.5
        # learn a mac address to avoid FLOOD next time.
        # self.mac_to_port[dpid][src] = in_port

        # v 1.0
        # learn a mac address to avoid FLOOD next time.
        self.mac_to_port[dpid][src] = msg.in_port


        if dst in self.mac_to_port[dpid]:
            out_port = self.mac_to_port[dpid][dst]
        else:
            out_port = ofproto.OFPP_FLOOD
            #print " Robim flooding"
            #self.logger.info("packet in %s ... %s %s %s %s", src_ip, dpid, src, dst, in_port)

        actions = [parser.OFPActionOutput(out_port)]

        # v 1.5
        # install a flow to avoid packet_in next time
        # if out_port != ofproto.OFPP_FLOOD:
        #     match = parser.OFPMatch(in_port=in_port, eth_dst=dst)
        #     self.add_flow(datapath, 1, match, actions)
        #     print " Vytvoreny flow"
        #     self.logger.info("packet in %s ... %s %s %s %s", src_ip, dpid, src, dst, in_port)

        # v 1.0
            # install a flow to avoid packet_in next time
        if out_port != ofproto.OFPP_FLOOD:
            self.add_flow(datapath, msg.in_port, dst, src, actions)

        data = None
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data

        # v 1.5
        # match = parser.OFPMatch(in_port=in_port)
        #
        # out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
        #                           match=match, actions=actions, data=data)

        # v 1.0
        out = datapath.ofproto_parser.OFPPacketOut(
            datapath=datapath, buffer_id=msg.buffer_id, in_port=msg.in_port,
            actions=actions, data=data)

        datapath.send_msg(out)

        # TOBEDELETED Check print
        # if not confidence_list:
        #     print "There are not any known requesters :( "
        # else:
        #     for src_ip in confidence_list:
        #         print ("Requester", src_ip, " confidence value ", confidence_list[src_ip])

        # TOBEDELETED Check print
        # if not incoming_packetin_list:
        #     print "There are not any stored incoming time for packets"
        #  else:
        #     for arrival_time in incoming_packetin_list:
        #         print arrival_time, " : ", incoming_packetin_list[arrival_time]

    def confidence_award(self, ev):
        global confidence_list
        global default_confidence_value
        global incoming_packetin_list
        global total_count_per_timeslot
        global packet_in_counters_list

        msg = ev.msg
        pkt = packet.Packet(msg.data)
        src_ip = self.find_src_ip_add(pkt)

        if src_ip is None:
            return

        arrival_time = int(round(time.time() * 1000))

        self.update_packet_in_counter_list(src_ip)

        # store arrival time and source IP add
        # TODO export incoming_packet_list every 10 seconds and clean it
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
        else:
            # TODO if total request from sender in this time slot is more than threashold for him
            if packet_in_counters_list[src_ip] > threshold_user[src_ip]:
                # give him worse confidence value
                sem_confidence_list.acquire()
                confidence_list[src_ip] = alpha * confidence_list[src_ip] - 1
                sem_confidence_list.release()
                #reject this request
                self.blacklist_user(src_ip)
                # break function
                return
            # else
                #TODO if controller is not under attack
                    #sem_confidence_list.acquire()
                    #confidence_list[src_ip] = alpha*confidence_list[src_ip] + 1
                    #sem_confidence_list.release()
                #TODO else
                    #sem_confidence_list.acquire()
                    #confidence_list[src_ip] = alpha*confidence_list[src_ip] - 1
                    # sem_confidence_list.release()

            self.blacklist_user(src_ip)

            # TODO Apply update_min_max_confidence_value after each change of CF

            #TODO  TOBEDELETED delete this just a try
            packet_ratio = 0.9
            confidence_list[src_ip] = 0.9
            self.update_min_max_confidence_value(src_ip, packet_ratio)

        self.sorting_to_queues(ev)

    def blacklist_user(self, src_ip):
        global confidence_list
        global threshold_malicious_user

        # #TODO 2
        # if confidence_list[src_ip] < threshold_malicious_user:
        #     #TODO

    def sorting_to_queues(self, ev):
        global priority_buffer
        actual_total_buffer_length = 0

        msg = ev.msg
        pkt = packet.Packet(msg.data)
        src_ip = self.find_src_ip_add(pkt)

        if max_confidence_value[0] - min_confidence_value[0] == 0 or confidence_list[src_ip] - min_confidence_value[0] == 0:
            index_to_buffer = number_of_queues
        else:
            index_to_buffer = int(round(((float(confidence_list[src_ip]) - float(min_confidence_value[0])) / (float(max_confidence_value[0]) - float(min_confidence_value[0]))) * float(number_of_queues)))
            if index_to_buffer == 0:
                index_to_buffer = 1

        #TOBEDELETED
        # print "<<<<<<<<<<<<<<>>>>>>>>>>>>>>"
        # print "CONFIDENCE VALUE"
        # print confidence_list[src_ip]
        # print min_confidence_value[0]
        # print max_confidence_value[0]
        # print number_of_queues
        # print "INDEX TO BUFFER IS ...."
        # print index_to_buffer
        # print "<<<<<<<<<<<<<<>>>>>>>>>>>>>>"

        sem_priority_buffer.acquire()
        for i in range(1, number_of_queues + 1):
            actual_total_buffer_length = len(priority_buffer[i])

        if actual_total_buffer_length < total_buffers_length:
            priority_buffer[index_to_buffer].append(msg)
        elif index_to_buffer == 1:
            # TODO update list of rejected packets
            # TODO DELETE THESE PRINTS
            print "Neulozil som tento packet, lebo mal index 1"
        else:
            for i in range(1, index_to_buffer):
                if len(priority_buffer[i]) > 0:
                    print "!!REJECTED!!"
                    print priority_buffer[i]
                    # TODO update list of rejected packets
                    priority_buffer[i].pop()
                    priority_buffer[index_to_buffer].append(msg)
                    break
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
                    weight.append(int(round((len(priority_buffer[i]) / max(len(priority_buffer[1]), 1)) * (beta ** (i - 1)))))

                for i in range(1, number_of_queues + 1):
                    actual_buffer_length.append(len(priority_buffer[i]))
                sem_priority_buffer.release()

                #serve request from the buffer with the highest priority
                buffer_length = actual_buffer_length[number_of_queues]
                if buffer_length != 0:
                    for j in range(0, buffer_length):
                        self.create_flow(priority_buffer[number_of_queues].pop(0))

                #serve stored requests
                for i in range(number_of_queues - 1, 0, -1):
                    if weight[i] < actual_buffer_length[i]:
                        for j in range(0, weight[i]):
                            self.create_flow(priority_buffer[i].pop(0))
                    else:
                        buffer_length = actual_buffer_length[i]
                        for j in range(0, buffer_length):
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

    # TODO TOBEDELETED COUNT RATIO FUNCTION

    # def count_ratio(self, arrival_time, src_ip):
    #     global incoming_packetin_list
    #     global time_slot
    #     packet_count_in_timeslot = 0
    #     count_of_src_ip_in_timeslot = 0
    #
    #     sem_incoming_packetin_list.acquire()
    #     for key in incoming_packetin_list:
    #         # print "*************************"
    #         # print "Key          ", key
    #         # print "Arrival time ", arrival_time
    #         # print "Rozdiel      ", arrival_time - time_slot
    #
    #         if (key >= (arrival_time - time_slot)) and key <= arrival_time:
    #             packet_count_in_timeslot = packet_count_in_timeslot + 1
    #
    #             # TODO pridat ked bude viacej zaznamov src_ip v jednom case
    #
    #             if src_ip in incoming_packetin_list[key]:
    #                 count_of_src_ip_in_timeslot = count_of_src_ip_in_timeslot + 1
    #     sem_incoming_packetin_list.release()
    #
    #     # print "Count of SRC IP ", count_of_src_ip_in_timeslot
    #     # print "Count of ALL ", packet_count_in_timeslot
    #     # return str(count_of_src_ip_in_timeslot) + " / " + str(packet_count_in_timeslot)
    #     return float(1 - float(count_of_src_ip_in_timeslot) / float(packet_count_in_timeslot))

    def update_min_max_confidence_value(self, src_ip, new_value):
        global min_confidence_value
        global max_confidence_value

        if len(min_confidence_value) == 1 and len(max_confidence_value) == 1:
            min_confidence_value = (new_value, src_ip)
            max_confidence_value = (new_value, src_ip)
            # TOBEDELETED
            # print ">>>>>>>>>MIN CONFIDENCE VALUE>>>>>>>>>>>"
            # print min_confidence_value
            # print ">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>"

        elif min_confidence_value[0] > new_value or min_confidence_value[1] == src_ip:
            min_confidence_value = (new_value, src_ip)

        elif max_confidence_value[0] < new_value or max_confidence_value[1] == src_ip:
            max_confidence_value = (new_value, src_ip)

    # TODO apply update_min_max_confidence_value to code :)
    # TODO spravit funkciu na zmenu min alebo max CF ak sa rejectne request

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

        while True:
            time.sleep(1)

            #TOBEDELETED
            # for src_ip in packet_in_counters_list:
            #     print src_ip, packet_in_counters_list[src_ip]
            #
            #
            # summary = 0
            # for x in packet_in_counters_list:
            #     summary += packet_in_counters_list[x]
            #
            # print("--- %s", summary)
            #TODO at the end of each time slot update threshold for user and CV
            sem_packet_in_counters_list.acquire()
            packet_in_counters_list = {}
            sem_packet_in_counters_list.release()

            sem_total_count_per_timeslot.acquire()
            total_count_per_timeslot = 0
            sem_total_count_per_timeslot.release()


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
from ryu.ofproto import ofproto_v1_5
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import ether_types
from ryu.lib.packet import ipv4
from ryu.lib.packet import arp
import threading
import time

incoming_packetin_list = {}
confidence_list = {}
default_confidence_value = 1

class SimpleSwitch15(app_manager.RyuApp):


    OFP_VERSIONS = [ofproto_v1_5.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(SimpleSwitch15, self).__init__(*args, **kwargs)
        self.mac_to_port = {}

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

        msg = ev.msg

        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']

        pkt = packet.Packet(msg.data)
        src_ip = self.find_src_ip_add(pkt)

        eth = pkt.get_protocols(ethernet.ethernet)[0]

        if src_ip is not None:
            print pkt

        if eth.ethertype == ether_types.ETH_TYPE_LLDP:
            # ignore lldp packet
            return
        dst = eth.dst
        src = eth.src

        dpid = datapath.id

        #------------
        self.confidence_award(ev)
        # ------------

        self.mac_to_port.setdefault(dpid, {})

        self.logger.info("packet in %s ... %s %s %s %s", src_ip, dpid, src, dst, in_port)

        print "\n-----------------------------\n"

        # learn a mac address to avoid FLOOD next time.
        self.mac_to_port[dpid][src] = in_port

        if dst in self.mac_to_port[dpid]:
            out_port = self.mac_to_port[dpid][dst]
        else:
            out_port = ofproto.OFPP_FLOOD

        actions = [parser.OFPActionOutput(out_port)]

        # install a flow to avoid packet_in next time
        if out_port != ofproto.OFPP_FLOOD:
            match = parser.OFPMatch(in_port=in_port, eth_dst=dst)
            self.add_flow(datapath, 1, match, actions)

        data = None
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data

        match = parser.OFPMatch(in_port=in_port)

        out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                  match=match, actions=actions, data=data)
        datapath.send_msg(out)

        if not confidence_list:
            print "There are not any known requesters :( "
        else:
            for src_ip in confidence_list:
                print ("Requester", src_ip, " confidence value ", confidence_list[src_ip])

        if not incoming_packetin_list:
            print "There are not any stored incoming time for packets"
        else:
            for arrival_time in incoming_packetin_list:
                print arrival_time, " : ", incoming_packetin_list[arrival_time]


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

    def confidence_award(self, ev):
        global confidence_list
        global default_confidence_value
        global incoming_packetin_list

        msg = ev.msg
        pkt = packet.Packet(msg.data)
        src_ip = self.find_src_ip_add(pkt)

        if src_ip is None:
            return

        arrival_time = int(round(time.time() * 1000))

        #store arrival time and source IP add
        if arrival_time not in incoming_packetin_list:
            incoming_packetin_list[arrival_time] = [src_ip]
        else:
            incoming_packetin_list[arrival_time].append(src_ip)


        if src_ip not in confidence_list:
            confidence_list[src_ip] = default_confidence_value
        else:
            packet_ratio = self.count_ratio(arrival_time, src_ip)
            confidence_list[src_ip] = 5

    def count_ratio(self, arrival_time, src_ip):
        global incoming_packetin_list

        for key in incoming_packetin_list:
        #TODO
        return 1

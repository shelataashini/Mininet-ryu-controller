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

"""
An OpenFlow 1.0 L2 learning switch implementation.
"""


from ryu.base import app_manager
from ryu.controller import ofp_event
import ryu.app.ofctl.api as api
from ryu.controller.handler import MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_0
from ryu.lib.mac import haddr_to_bin
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet, arp
from ryu.lib.packet import ether_types



class SimpleSwitch(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_0.OFP_VERSION]
    
   
    def __init__(self, *args, **kwargs):
        super(SimpleSwitch, self).__init__(*args, **kwargs)
        self.mac_to_port = {}

    def add_flow(self, datapath, in_port, dst, actions):
        ofproto = datapath.ofproto

        match = datapath.ofproto_parser.OFPMatch(
            in_port=in_port, dl_dst=haddr_to_bin(dst))


        mod = datapath.ofproto_parser.OFPFlowMod(
            datapath=datapath, match=match, cookie=0,
            command=ofproto.OFPFC_ADD, idle_timeout=0, hard_timeout=0,
            priority=ofproto.OFP_DEFAULT_PRIORITY,
            flags=ofproto.OFPFF_SEND_FLOW_REM, actions=actions)
        
        datapath.send_msg(mod) 

    def arp_reply(self,datapath, src, dst, dst_ip, src_ip, eth, msg):#function used to generate the arp-replies by the controller
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        pkt = packet.Packet()
        pkt.add_protocol(ethernet.ethernet(ethertype=eth.ethertype, dst=src, src=dst))
        pkt.add_protocol(arp.arp(opcode=2, src_mac=dst, src_ip=dst_ip, dst_mac=src, dst_ip=src_ip))#OPCODE 2 signifies that we are generating arp-replies
        pkt.serialize()#used to serialize the generated packet.
        self.logger.info("packet-out %s", pkt)

        actions = [parser.OFPActionOutput(port=msg.in_port)]
        data = pkt.data
     
        out = parser.OFPPacketOut(datapath=datapath,
                                  buffer_id=ofproto.OFP_NO_BUFFER,
                                  in_port=ofproto.OFPP_CONTROLLER,
                                  actions=actions,
                                  data=data)
        datapath.send_msg(out)
        #self.logger.info("executed for dpid %s", datapath.id)

    def add_entry(self, datapath, in_port, dst, out_port):
        ofproto = datapath.ofproto
        actions = [datapath.ofproto_parser.OFPActionOutput(out_port)]
        self.add_flow(datapath, in_port, dst, actions)


    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocol(ethernet.ethernet)
        pkt_arp = pkt.get_protocol(arp.arp)

        dst = eth.dst
        src = eth.src
        dpid = datapath.id
      
        datapath_s2 = api.get_datapath(self,2)
              
        if eth.ethertype == ether_types.ETH_TYPE_LLDP:
            # ignore lldp packet
            return
        
        if eth.ethertype == ether_types.ETH_TYPE_ARP:
            self.logger.info("arp dpid %s", datapath.id)
            if pkt_arp.opcode == arp.ARP_REQUEST:
              dst_ip = pkt_arp.dst_ip
              src_ip = pkt_arp.src_ip
                  
              if dpid == 1:  
               self.arp_reply(datapath, src, '00:00:00:00:00:02', dst_ip, src_ip, eth, msg)   #arp reply to h1
               self.add_entry(datapath, 1, '00:00:00:00:00:02', 2)  #adding entries to switch 1 and 2
               self.add_entry(datapath, 2, '00:00:00:00:00:01', 1)
               self.add_entry(datapath_s2, 1, '00:00:00:00:00:01', 2)
               self.add_entry(datapath_s2, 2, '00:00:00:00:00:02', 1)

              if dpid == 2:
               self.arp_reply(datapath, src, '00:00:00:00:00:01', dst_ip, src_ip, eth, msg)   #arp reply to  h2
                  
          
            

   

#!/usr/bin/python3

import asyncio
from cougarnet.sim.host import BaseHost


import os
import json
import struct

VLAN_1Q_IDENTIFIER = 0x8100
AGING_TIME = 8

class Switch(BaseHost):
    def __init__(self):
      super().__init__()
      self._outgoing = {}
      self._remove_events = {}
      self._vlans = {}
      self._intfs = {}
      self._trunks = set()

      blob = os.environ.get('COUGARNET_VLAN', '')
      if blob: # If configuration file includes VLAN
        vlan_info = json.loads(blob)
        for myint in self.physical_interfaces:
          val = vlan_info[myint]
          if val == 'trunk':
            self._trunks.add(myint)
          else:
            vlan_val = int(val[4:]) # Extract the VLAN id from 802.1Q header
            if vlan_val not in self._vlans:
                self._vlans[vlan_val] = [] # Initialize to empty list so interfaces on same VLAN grouping can be added later on 

            self._vlans[vlan_val].append(myint)
            self._intfs[myint] = vlan_val
      else:
        for myint in self.physical_interfaces:
          vlan_val = 1
          if vlan_val not in self._vlans:
              self._vlans[vlan_val] = []
          
          self._vlans[vlan_val].append(myint)
          self._intfs[myint] = vlan_val


    
    def create_802_1Q_frame(self, vlan_id):
       frame = b''

       frame += struct.pack("!H", VLAN_1Q_IDENTIFIER)
       all_ones_16_bit = 2**16 - 1
       frame += struct.pack("!H", all_ones_16_bit & vlan_id) # Idea is 1111-1111-1111 & ####-####-#### => 0000 - ####-####-#### where vlan_id is represents the the 12 hashtags!

       return frame


    def _handle_frame(self, frame: bytes, intf: str) -> None:
      src = frame[6:12]
      dst = frame[:6]

      vlan = None # Initialize VLAN to be used in other parts of handle frame 

      if intf in self._trunks:
        vlan = struct.unpack('!H', frame[14:16])[0] # Get VLAN of intf that this frame was received on from 802 header 
        frame = frame[:12] + frame[16:]
      else:
        vlan = self._intfs[intf] # Get the VLAN of intf that this frame was received on from mapping if not a trunk port

      if dst in self._outgoing:
        if self._outgoing[dst] in self._trunks:
          frame = dst + src + self.create_802_1Q_frame(vlan) + frame[16:] # Need to send header if sending to outgoing trunk port

        self.send_frame(frame, self._outgoing[dst])
      else:
        for myint in self.physical_interfaces:
          if intf != myint and (myint in self._trunks or self._intfs[myint] == vlan):
            if myint in self._trunks:
              fr = dst + src + self.create_802_1Q_frame(vlan) + frame[16:] # Need to send header if sending to other interface(s) that are trunk ports

            else:
              fr = frame # Already stripped from frame when checking on receiving end that this port isn't trunk

            self.send_frame(fr, myint)
        

      self._outgoing[src] = intf
      ev = self._remove_events.get(src, None)

      if ev is not None:
          ev.cancel()
      loop = asyncio.get_event_loop()

      self._remove_events[src] = loop.call_later(AGING_TIME, self.del_outgoing, src)

    def del_outgoing(self, src):
        del self._outgoing[src]

def main():
    Switch().run()

if __name__ == '__main__':
    main()

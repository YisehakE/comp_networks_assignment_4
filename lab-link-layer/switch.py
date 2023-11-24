#!/usr/bin/python3

import asyncio
from cougarnet.sim.host import BaseHost


import os
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
            #TODO: Add one line of code to handle this if statement.
            self._trunks.add(myint) # ------- TODO: check if logic correct
          else:
            vlan_val = int(val[4:]) # Extract the VLAN id from 802.1Q header ------- TODO: check if logic correct
            if vlan_val not in self._vlans:
                #TODO: Add one line of code to handle this if statement.
                self._vlans[vlan_val] = [] # Initialize to empty list so interfaces can be ------- TODO: check if logic correct

            self._vlans[vlan_val].append(myint) # ------- TODO: check if logic correct
            self._intfs[myint] = vlan_val
      else:
        for myint in self.physical_interfaces:
          vlan_val = 1
          if vlan_val not in self._vlans:
              self._vlans[vlan_val] = []
          
          #TODO: Finish filling in the code for the for loop. Hint: it has to do with handling vlan_val and is only 2 lines of code.
          self._vlans[vlan_val].append(myint)
          self._intfs[myint] = vlan_val


    
    def create_802_1Q_frame(self, vlan_id):
       
       frame = b''

       frame += struct.pack("!H", VLAN_1Q_IDENTIFIER)
       zero_16_bit = f'{0:016b}' # https://stackoverflow.com/questions/10411085/converting-integer-to-binary-in-python
       frame += struct.pack("!H", zero_16_bit | vlan_id) # Idea is 0000-0000-0000 | ####-####-#### => 0000 - ####-####-#### where vlan_id is represents the the 12 hashtags!

       return frame
    
    def create_ethernet_frame(self, dst, src, eth_type, payload, vlan_802_1Q_hdr = None):
       
      frame = b''
      frame += dst if type(dst) is bytes else struct.pack("!13s", dst)
      frame += src if type(dst) is bytes else struct.pack("!13s", src)

      frame += vlan_802_1Q_hdr if vlan_802_1Q_hdr else b''

      frame += eth_type if type(eth_type) is bytes else struct.pack("!H", eth_type)
      frame += payload if type(payload) is bytes else bytes(payload)

      return frame

    def _handle_frame(self, frame: bytes, intf: str) -> None:
      src = frame[6:12]
      dst = frame[:6]

      type = frame[12:14] or frame[18:20] # The latter is if frame includes 802.1Q header 
      payload = frame[14:] or frame[20:] # The latter is if frame includes 802.1Q header 
      vlan = None # Initialize vlan to be used in other parts of handle frame 

      if intf in self._trunks:
        vlan = struct.unpack('!H', frame[14:16])[0]
        frame = frame[:12] + frame[16:]
      else:
        vlan = self._intfs[intf] # Why do we set interface mapping to a VLAN even if this switch is not a trunk

      if dst in self._outgoing:
        if self._outgoing[dst] in self._trunks:
          #TODO: complete the following line
          frame = dst + src + self.create_802_1Q_frame(vlan) + frame[16:]

        self.send_frame(frame, self._outgoing[dst])
      else:
        for myint in self.physical_interfaces:
          if intf != myint and (myint in self._trunks or self._intfs[myint] == vlan):
            if myint in self._trunks:
              #TODO: Complete the following line
              fr = dst + src + self.create_802_1Q_frame(vlan) + frame[16:]

            else:
              fr = frame # Already stripped from frame when checking on receiving end that this port isn't trunk ---- TODO: check if logic is correct

            self.send_frame(fr, myint)
        

      self._outgoing[src] = intf
      ev = self._remove_events.get(src, None)

      if ev is not None:
          ev.cancel()
      loop = asyncio.get_event_loop()
      #Complete the following line/
      self._remove_events[src] = loop.call_later(AGING_TIME, self.del_outgoing, src)

    def del_outgoing(self, src):
        #TODO: Complete the following line.
        del self._outgoing[src]

def main():
    Switch().run()

if __name__ == '__main__':
    main()

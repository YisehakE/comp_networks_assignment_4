#!/usr/bin/python3

import asyncio
from cougarnet.sim.host import BaseHost

class Switch(BaseHost):
    def __init__(self):
        super().__init__()
        self._outgoing = {}
        self._remove_events = {}
        self._vlans = {}
        self._intfs = {}
        self._trunks = set()

        blob = os.environ.get('COUGARNET_VLAN', '')
        if blob:
            vlan_info = json.loads(blob)
            for myint in self.physical_interfaces:
                val = vlan_info[myint]
                if val == 'trunk':
                    #TODO: Add one line of code to handle this if statement.
                    
                else:
                    vlan_val = int(val[4:])
                    if vlan_val not in self._vlans:
                        #TODO: Add one line of code to handle this if statement.
                    self._vlans[vlan_val].append(myint)
                    self._intfs[myint] = vlan_val
        else:
            
            for myint in self.physical_interfaces:
                vlan_val = 1
                if vlan_val not in self._vlans:
                    self._vlans[vlan_val] = []
                #TODO: Finish filling in the code for the for loop. Hint: it has to do with handling vlan_val and is only 2 lines of code.

        

    def _handle_frame(self, frame: bytes, intf: str) -> None:
        src = frame[6:12]
        dst = frame[:6]

        if intf in self._trunks:
            vlan = struct.unpack('!H', frame[14:16])[0]
            frame = frame[:12] + frame[16:]
        else:
            vlan = self._intfs[intf]

        if dst in self._outgoing:
            if self._outgoing[dst] in self._trunks:
                #TODO: complete the following line
                #frame = 

            self.send_frame(frame, self._outgoing[dst])
        else:
            for myint in self.physical_interfaces:
                if intf != myint and \
                        (myint in self._trunks or self._intfs[myint] == vlan):
                    if myint in self._trunks:
                        #TODO: Complete the following line
                        #fr = 
                    else:
                        fr = frame

                    self.send_frame(fr, myint)
            
        self._outgoing[src] = intf
        ev = self._remove_events.get(src, None)
        if ev is not None:
            ev.cancel()
        loop = asyncio.get_event_loop()
        #Complete the following line/
        #self._remove_events[src] = 

    def del_outgoing(self, src):
        #TODO: Complete the following line.
        #del 

def main():
    Switch().run()

if __name__ == '__main__':
    main()

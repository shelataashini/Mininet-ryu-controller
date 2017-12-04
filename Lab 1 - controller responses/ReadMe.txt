Creating a topology as following:

                           Controller 
                           /       \ 
               h1  ------ s1 -----  s2 ----- h2

Create the topology using    sudo mn --topology=linear,2  --controller=remote  --mac
                    
Run h1 ping h2 after the controller is active.
 
 The ryu controller can be running by  ryu-manager <controller script>
 
The following requirements are to be fulfilled by the controller script:
1. When h1 sends the initial ARP, the controller shall respond this ARP (rather than h2). 
2. When initial ARP is received, the flow entries should be put in s1 and s2 in both ways to enable the channel. (In other words, only the ARP are sent to the controller).
3. The entries shall match against     (in_port, ether_type, ipv4_src, ipv4_dst). 

Note:

The table status can be obtained by running   sudo ovs-ofctl dump-flows <switch name: e.g. s1> after mininet is active.

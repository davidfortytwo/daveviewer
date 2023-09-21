#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author: David Espejo (Fortytwo Security)

import stun
import socket
import time

def use_stun():
    try:
        nat_type, external_ip, external_port = stun.get_ip_info(stun_host="stun.l.google.com", stun_port=19302)
        if external_ip:
            print(f"[STUN] NAT Type: {nat_type}")
            print(f"[STUN] External IP: {external_ip}")
            print(f"[STUN] External Port: {external_port}")
            return True
    except Exception as e:
        print(f"[STUN] Failed: {e}")
        return False

def use_turn():
    try:
        # Simulating a TURN server (Replace with actual TURN server details)
        turn_server_ip = "turn_server_ip_here"
        turn_server_port = 3478

        # Establish a connection to the TURN server
        # (Actual TURN implementation would be more complex)
        print(f"[TURN] Connecting to TURN server {turn_server_ip}:{turn_server_port}")
        return True
    except Exception as e:
        print(f"[TURN] Failed: {e}")
        return False

def use_hole_punching():
    try:
        # Simulating hole punching
        print("[Hole Punching] Attempting hole punching...")

        # Create UDP socket
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        # Simulate hole punching by sending a UDP packet to a peer
        # (Actual hole punching would involve coordination between peers)
        peer_ip = "peer_ip_here"
        peer_port = 12345
        udp_socket.sendto(b"Hello", (peer_ip, peer_port))

        print("[Hole Punching] Hole punched successfully.")
        return True
    except Exception as e:
        print(f"[Hole Punching] Failed: {e}")
        return False

if __name__ == "__main__":
    # Try STUN first
    if use_stun():
        print("STUN succeeded. Proceeding with connection.")
    else:
        print("STUN failed. Trying TURN...")
        
        # Try TURN next
        if use_turn():
            print("TURN succeeded. Proceeding with connection.")
        else:
            print("TURN failed. Trying Hole Punching...")
            
            # Try Hole Punching last
            if use_hole_punching():
                print("Hole Punching succeeded. Proceeding with connection.")
            else:
                print("All NAT traversal techniques failed.")

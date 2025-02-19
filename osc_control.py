"""
Govee LAN API with OSC Control
Author: Perplexity AI Research
Date: 2025-02-18
"""

import asyncio
import logging
from govee_led_wez import GoveeController, GoveeDevice, GoveeColor
from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import AsyncIOOSCUDPServer

class GoveeOSCController:
    def __init__(self):
        self.controller = GoveeController()
        self.active_devices = []
        self.current_color = {'r': 0, 'g': 0, 'b': 0}
        self.discovered_devices = set()

    async def send_current_color(self):
        """Send the current color to all devices"""
        if not self.active_devices:
            return

        color = GoveeColor(self.current_color['r'], 
                          self.current_color['g'],
                          self.current_color['b'])
        
        tasks = [self.controller.set_color(device, color) 
                for device in self.active_devices]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for device, result in zip(self.active_devices, results):
            if isinstance(result, Exception):
                print(f"Error on {device.device_id}: {str(result)}")
            else:
                status = "Success" if result else "Failed"
                print(f"{status}: {device.device_id} -> {color}")

    def handle_osc_message(self, address: str, *args):
        """Process incoming OSC messages"""
        component = address.split('/')[-1].lower()
        try:
            if component in ('r', 'g', 'b') and args:
                value = max(0, min(255, int(args[0])))
                self.current_color[component] = value
                asyncio.create_task(self.send_current_color())
        except (ValueError, TypeError):
            print(f"Invalid OSC value: {args}")

async def control_lights():
    govee_ctl = GoveeOSCController()
    osc_ip = "0.0.0.0"  # Listen on all network interfaces
    osc_port = 5005      # Default OSC port

    # Configure OSC server
    dispatcher = Dispatcher()
    dispatcher.map("/color/*", govee_ctl.handle_osc_message)
    
    # Device discovery callback
    def device_found(device: GoveeDevice):
        if device.device_id not in govee_ctl.discovered_devices:
            print(f"Discovered: {device.device_id}")
            govee_ctl.discovered_devices.add(device.device_id)

    try:
        # Start device discovery
        govee_ctl.controller.set_device_change_callback(device_found)
        govee_ctl.controller.start_lan_poller()
        print("Discovering devices for 5 seconds...")
        await asyncio.sleep(5)
        govee_ctl.controller.set_device_change_callback(None)

        # Get active devices
        govee_ctl.active_devices = [
            d for d in govee_ctl.controller.devices.values()
            if d.device_id in govee_ctl.discovered_devices
        ]

        if not govee_ctl.active_devices:
            print("No Govee devices found")
            return

        # Start OSC server
        server = AsyncIOOSCUDPServer(
            (osc_ip, osc_port), 
            dispatcher, 
            asyncio.get_event_loop()
        )
        transport, protocol = await server.create_serve_endpoint()
        
        print(f"Listening for OSC messages on {osc_ip}:{osc_port}")
        print("Send OSC messages to /color/r, /color/g, /color/b")
        
        # Keep running until interrupted
        while True:
            await asyncio.sleep(3600)  # Sleep indefinitely

    except asyncio.CancelledError:
        print("\nShutting down...")
    finally:
        transport.close()
        govee_ctl.controller.stop()
        print("Controller shutdown complete")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(control_lights())
    except KeyboardInterrupt:
        print("\nExited by user")

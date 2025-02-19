"""
Govee LAN API Color Control Script
Author: Perplexity AI Research
Date: 2025-02-18
"""

import asyncio
import logging
from govee_led_wez import GoveeController, GoveeDevice, GoveeColor

async def control_lights():
    controller = GoveeController()
    discovered_devices = set()  # Use set to prevent duplicates

    def device_found(device: GoveeDevice):
        """Callback with duplicate prevention"""
        if device.device_id not in discovered_devices:
            print(f"Discovered: {device.device_id}")
            discovered_devices.add(device.device_id)

    controller.set_device_change_callback(device_found)
    
    try:
        print("Starting discovery...")
        controller.start_lan_poller()
        
        # Limited discovery window
        await asyncio.sleep(5)
        #set device change callback to none
        controller.set_device_change_callback(None)
        
        if not discovered_devices:
            print("No devices found")
            return

        # Get fresh device objects from controller
        active_devices = [d for d in controller.devices.values() 
                         if d.device_id in discovered_devices]
        
        # Single-pass color change
        for device in active_devices:
            print(f"Processing {device.device_id}")
            success = await controller.set_color(
                device,
                GoveeColor(255, 0, 0)
            )
            if success:
                print(f"Success: ({device.device_id}) set to red")
            else:
                print(f"Failed: Verify ({device.device_id}) supports color control")

    finally:
        controller.stop()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(control_lights())

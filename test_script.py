"""
Govee LAN API Color Control Script
Author: Perplexity AI Research
Date: 2025-02-18
"""

import asyncio
import logging
from govee_led_wez import GoveeController, GoveeDevice, GoveeColor

async def control_lights():
    """Main function to discover and control Govee devices"""
    controller = GoveeController()
    discovered_devices = []

    def device_found(device: GoveeDevice):
        """Callback for newly discovered devices"""
        print(f"Discovered: ({device.device_id})")
        discovered_devices.append(device)

    # Configure discovery callback
    controller.set_device_change_callback(device_found)
    
    try:
        # Start LAN discovery
        controller.start_lan_poller()
        print("Scanning network for Govee devices (15s)...")
        
        # Allow time for discovery
        await asyncio.sleep(15)
        
        if not discovered_devices:
            print("No devices found. Verify:")
            print("- Devices are powered on")
            print("- LAN control enabled in Govee Home app")
            print("- Connected to same 2.4GHz network")
            return

        # Set all found devices to red
        for device in discovered_devices:
            print(f"Attempting color change for {device.device_id}")
            success = await controller.set_color(
                device,
                GoveeColor(255, 0, 0)  # Red values
            )
            
            if success:
                print(f"Success: ({device.device_id}) set to red")
            else:
                print(f"Failed: Verify ({device.device_id}) supports color control")

    finally:
        controller.stop()
        print("Controller shutdown complete")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(control_lights())

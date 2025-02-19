"""
Govee LAN API Interactive Color Control (Continuous)
Author: Perplexity AI Research
Date: 2025-02-18
"""

import asyncio
import logging
from govee_led_wez import GoveeController, GoveeDevice, GoveeColor
import aioconsole #aioconsole-0.8.1 at install time

async def get_rgb_input():
    """Get and validate RGB input with exit handling"""
    while True:
        try:
            rgb_str = await aioconsole.ainput(
                "\nEnter RGB values (0-255) as comma-separated numbers\n"
                "or type 'exit' to quit: "
            )
            
            if rgb_str.lower() == 'exit':
                return None
                
            r, g, b = map(int, rgb_str.split(','))
            if all(0 <= val <= 255 for val in (r, g, b)):
                return GoveeColor(r, g, b)
                
            print("Error: Values must be between 0-255")
        except (ValueError, TypeError):
            print("Invalid format. Example: 255,120,0")

async def color_control_loop(controller, devices):
    """Continuous color update loop"""
    while True:
        target_color = await get_rgb_input()
        if not target_color:
            return  # Exit on 'exit' command
            
        print(f"\nSetting color to {target_color}")
        tasks = [controller.set_color(device, target_color) for device in devices]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for device, result in zip(devices, results):
            if isinstance(result, Exception):
                print(f"Error on {device.device_id}: {str(result)}")
            else:
                status = "Success" if result else "Failed"
                print(f"{status}: {device.device_id}")

async def control_lights():
    controller = GoveeController()
    discovered_devices = set()

    def device_found(device: GoveeDevice):
        if device.device_id not in discovered_devices:
            print(f"Discovered: {device.device_id}")
            discovered_devices.add(device.device_id)

    try:
        # Device discovery phase
        controller.set_device_change_callback(device_found)
        controller.start_lan_poller()
        print("Discovering devices for 5 seconds...")
        await asyncio.sleep(5)
        controller.set_device_change_callback(None)
        
        if not discovered_devices:
            print("No devices found")
            return

        active_devices = [d for d in controller.devices.values() 
                         if d.device_id in discovered_devices]
        
        # Start interactive control loop
        await color_control_loop(controller, active_devices)
        
    except asyncio.CancelledError:
        print("\nShutting down...")
    finally:
        controller.stop()
        print("Controller shutdown complete")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(control_lights())
    except KeyboardInterrupt:
        print("\nExited by user")

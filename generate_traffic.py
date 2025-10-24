#!/usr/bin/env python

"""
Simple Traffic Generation Script for CARLA - Part 3
"""

import glob
import os
import sys
import time

try:
    sys.path.append(glob.glob('../carla/dist/carla-*%d.%d-%s.egg' % (
        sys.version_info.major,
        sys.version_info.minor,
        'win-amd64' if os.name == 'nt' else 'linux-x86_64'))[0])
except IndexError:
    pass

import carla
import random

def main():
    vehicles_list = []
    walkers_list = []
    all_id = []
    client = carla.Client('localhost', 2000)
    client.set_timeout(10.0)

    try:
        world = client.get_world()
        
        print('\n--- Setting up Traffic Manager ---')
        traffic_manager = client.get_trafficmanager(8000)
        traffic_manager.set_global_distance_to_leading_vehicle(2.5)
        traffic_manager.set_synchronous_mode(True)
        
        settings = world.get_settings()
        settings.synchronous_mode = True
        settings.fixed_delta_seconds = 0.05
        world.apply_settings(settings)

        blueprints = world.get_blueprint_library().filter('vehicle.*')
        blueprintsWalkers = world.get_blueprint_library().filter('walker.pedestrian.*')
        
        spawn_points = world.get_map().get_spawn_points()
        number_of_vehicles = 50
        number_of_walkers = 30

        # Spawn vehicles
        print(f'\n--- Spawning {number_of_vehicles} vehicles ---')
        for n, transform in enumerate(spawn_points):
            if n >= number_of_vehicles:
                break
            blueprint = random.choice(blueprints)
            if blueprint.has_attribute('color'):
                color = random.choice(blueprint.get_attribute('color').recommended_values)
                blueprint.set_attribute('color', color)
            if blueprint.has_attribute('driver_id'):
                driver_id = random.choice(blueprint.get_attribute('driver_id').recommended_values)
                blueprint.set_attribute('driver_id', driver_id)
            
            vehicle = world.try_spawn_actor(blueprint, transform)
            if vehicle is not None:
                vehicle.set_autopilot(True, traffic_manager.get_port())
                vehicles_list.append(vehicle.id)
        
        print(f'Spawned {len(vehicles_list)} vehicles with autopilot\n')

        # Spawn walkers
        print(f'--- Spawning {number_of_walkers} walkers ---')
        spawn_points_walkers = []
        for i in range(number_of_walkers):
            spawn_point = carla.Transform()
            loc = world.get_random_location_from_navigation()
            if loc is not None:
                spawn_point.location = loc
                spawn_points_walkers.append(spawn_point)

        # Spawn walker objects
        for spawn_point in spawn_points_walkers:
            walker_bp = random.choice(blueprintsWalkers)
            walker = world.try_spawn_actor(walker_bp, spawn_point)
            if walker is not None:
                walkers_list.append(walker.id)
        
        # Spawn walker controllers
        walker_controller_bp = world.get_blueprint_library().find('controller.ai.walker')
        for walker_id in walkers_list:
            controller = world.spawn_actor(walker_controller_bp, carla.Transform(), attach_to=world.get_actor(walker_id))
            all_id.append(controller.id)
        
        all_actors = world.get_actors(all_id)
        world.tick()
        
        # Start walkers
        for i in range(len(all_actors)):
            all_actors[i].start()
            all_actors[i].go_to_location(world.get_random_location_from_navigation())
            all_actors[i].set_max_speed(1.4)
        
        print(f'Spawned {len(walkers_list)} walkers\n')
        print('--- Traffic generation complete! ---')
        print('Vehicles are driving with autopilot')
        print('Pedestrians are walking around')
        print('\nPress Ctrl+C to stop...\n')

        # Keep simulation running
        while True:
            world.tick()
            time.sleep(0.05)

    except KeyboardInterrupt:
        print('\n--- Stopping simulation ---')
    finally:
        print('Cleaning up...')
        settings = world.get_settings()
        settings.synchronous_mode = False
        world.apply_settings(settings)
        
        print('Destroying vehicles...')
        client.apply_batch([carla.command.DestroyActor(x) for x in vehicles_list])
        
        print('Destroying walkers...')
        for i in range(0, len(all_id), 2):
            all_actors[i].stop()
        client.apply_batch([carla.command.DestroyActor(x) for x in all_id])
        
        print('Done!\n')

if __name__ == '__main__':
    main()

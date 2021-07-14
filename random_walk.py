#!/usr/bin/env python3

############################################################################
#
# MODULE:       r.random_walk
# AUTHOR:       Corey White, Center for Geospatial Analytics, North Carolina State University
# PURPOSE:      Performs a random walk on a raster surface.
# COPYRIGHT:    (C) 2021 Corey White
#               This program is free software under the GNU General
#               Public License (>=v2). Read the file COPYING that
#               comes with GRASS for details.
#
#############################################################################

#%module
#% description: Performs a random-walk on a given input raster and returns the resulting walk.
#% keyword: raster
#% keyword: select
#% keyword: random walk
#%end

#%flag
#% key: revisit
#% description: Allow walker to revisit a cell.
#%end

#%option G_OPT_R_INPUT
#%label: Name of raster map to use as walk surface
#%key: input
#%end

#%option G_OPT_R_OUTPUT
#%end

#%option
#% key: steps
#% type: integer
#% required: no
#% multiple: no
#% description: How many steps to take during walk.
#% answer: 100000
#%end

#%option
#% key: directions
#% type: string
#% required: no
#% multiple: no
#% options: 4-dir, 8-dir
#% description: How many directions should be used during walk.
#% answer: 4-dir
#%end

#%option
#% key: memory
#% type: integer
#% required: no
#% multiple: no
#% description: How much memory to use.
#% answer: 10000
#%end

#%option
#% key: seed
#% type: integer
#% required: no
#% multiple: no
#% description: Set random seed
#% answer: 1
#%end


import sys

import grass.script as gs
from grass.pygrass import raster
from grass.pygrass.gis.region import Region
from grass.exceptions import CalledModuleError
import random
import math
#import numpy as np

class GetOutOfLoop( Exception ):
    """
    Throw to break out of nested loop.
    """
    pass

def take_step(current_position, num_dir, black_list = None):
    """
    Calculates the next position of walker using either 4 or 8 possible directions.
    :param list[row, column] current_position: A list with current row and column as integers.
    :param int num_dir: The number of directions used in walk. Value must be either 4 or 8.
    :return list[row, column] new_position
    """
    if black_list == None:
        black_list = []
    direction = random.choice([ele for ele in range(num_dir) if ele not in black_list])

    current_row = current_position[0]
    current_column = current_position[1]
    new_position = []
    # 4 - directions
    #direction = random.randint(0, num_dir)
    if direction == 0:
        # Move up
        new_position = [current_row + 1,current_column]
    elif direction == 1:
        # Move right
        new_position = [current_row,current_column + 1]
    elif direction == 2:
        # Move Down
        new_position = [current_row - 1,current_column]
    elif direction == 3:
        # Move Left
        new_position = [current_row,current_column - 1]
    elif direction == 4:
        # Move Top Right
        new_position = [current_row + 1,current_column + 1]
    elif direction == 5:
        # Move Bottom Right
        new_position = [current_row - 1,current_column + 1]
    elif direction == 6:
        # Move Bottom Left
        new_position = [current_row - 1,current_column - 1]
    elif direction == 7:
        # Move Top Left
        new_position = [current_row + 1,current_column - 1]
    else:
        raise ValueError(f'Unsupported Direction Recieved: {direction}')

    return {'position':new_position, 'direction': direction}

def cell_visited(rast, position):
    """
    Checks if a cell was previously visited during walk.
    :param RasterSegment rast: The new raster that walk results are written.
    :param list[row, column]: The position to check.
    :return bool
    """
    cell_value = rast.get(position[0], position[1])
    # Positions with a value greater than zero are visited.
    return cell_value > 0

def walker_is_stuck(tested_directions, num_directions):
    """
    Test if walker has no more move to consider and is stuck.
    :param list tested_directions: List of directions previously tested
    :param int num_directions: The total number of possible directions (4 or 8)
    :return bool
    """
    return len(tested_directions) == num_directions

def find_new_path(walk_output, current_pos, new_position, num_directions, step):
    """
    Finds a cell that walker has not touched yet.
    :param RasterSegment walk_output: The raster being written
    :param list[row, column] current_position: The current position of the walker.
    :param Dict{position: list[row, column], direction: int} new_position: Previously test position
    :param int num_directions: The total number of directions walker can travel 4 or 8.
    :param int step: The current step the walker is on.
    """
    tested_directions = []
    visited = cell_visited(walk_output, new_position['position'])
    tested_directions.append(new_position['direction'])
 
    while visited:
        if walker_is_stuck(tested_directions, num_directions):
            print(f'Walker stuck on step {step}')
            raise GetOutOfLoop
        else:
            # continue to check cells for an unvisited cell until one is found or walker is stuck
            new_position = take_step(current_pos, num_directions, tested_directions)
            tested_directions.append(new_position['direction'])
            visited = cell_visited(walk_output, new_position['position'])
    
    return new_position

def random_walk(num_directions, start_pos, walk_output, steps, revisit):
    """
    Calulates a random walk on a raster surface.
    :param int num_directions: The number of directions to consider on walk. 
        Values represtent either 4 or 8 direction walks and must be set as
        either 4 or 8.
    :param list[row, column] start_pos:
    :param RasterSegment walk_output:
    :param int steps:
    :param bool revisit: Determines if the walker can revisit a cell it has
        already visited.
    :return RasterSegment
    """
    # Random Walk 
    print(f'Starting Random Walk')
    
    
    # Select Random Starting Cell in Matrix
    start_pos = starting_position(start_pos[0], start_pos[1])
    #print(f'Starting Position: {start_pos}')
    walk_output.put(start_pos[0],start_pos[1], 2)
    # Walk 100000 steps
    current_pos = start_pos
    try:
        for step in range(steps + 1):
            # Take a randomly selected step in a direction
            new_position = take_step(current_pos, num_directions)
            
            
            if revisit == False:
                # Don't allow walker to revisit same cell.
                new_position = find_new_path(walk_output, current_pos, new_position, num_directions, step)
                
            
            value = walk_output[new_position['position'][0], new_position['position'][1]]
            # Add up times visited
            walk_output[new_position['position'][0], new_position['position'][1]] = value + 1
                
            # Update Position
            current_pos = new_position['position']

    except GetOutOfLoop:
        # Mark the last step if walker gets stuck
        walk_output[current_pos[0], current_pos[1]] = 3
        pass
        
    return walk_output

def starting_position(surface_rows, surface_columns):
    """
    Calculates a random starting position for walk.
    :param int surface_rows: The total number of rows to consider.
    :param int surface_columns: The total number of columns to consider.
    :return list[row, column]
    """
    start_row = random.randint(0, surface_rows)
    start_column = random.randint(0, surface_columns)
    #print(f'Start row {start_row}, start column {start_column}')
    return [start_row, start_column]

def main():
    options, flags = gs.parser()

    input_raster = options['input']
   

    output_raster = options['output']

    steps = int(options['steps'])

    directions_option = options['directions']
    
    # Set numerical values for directions
    directions = 4 if directions_option == '4-dir' else 8
    
    memory = options['memory']

    seed = options['seed']
    random.seed(seed)

    # check for revisit flag
    revisit = flags['r']

    #surface = raster.RasterSegment(input_raster, maxmem=memory)
    #surface.open()
    #surface_rows = surface._rows
    #surface_columns = surface._cols
    
    print(f'Creating Performing Walk on Surface with {surface_rows} rows and {surface_columns} columns')
    
    walk_output = raster.RasterSegment(output_raster, maxmem=memory)
    walk_output.open('w', mtype='CELL', overwrite=True)
    
    reg = Region()
    cols = reg.cols
    rows = reg.rows
    print(f'Region with {rows} rows and {cols} columns')
    walk_output = random_walk(directions,[rows, cols],walk_output, steps, revisit)
    walk_output.close()


if __name__ == "__main__":
    sys.exit(main())
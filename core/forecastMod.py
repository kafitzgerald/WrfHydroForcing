from core import errMod
import datetime
import os
import sys

def process_forecasts(ConfigOptions,wrfHydroGeoMeta,inputForcingMod,mpiMeta):
    """
    Main calling module for running realtime forecasts and re-forecasts.
    :param jobMeta:
    :return:
    """
    # Loop through each WRF-Hydro forecast cycle being processed. Within
    # each cycle, perform the following tasks:
    # 1.) Loop over each output frequency
    # 2.) Determine the input forcing cycle dates (both before and after)
    #     for temporal interpolation, downscaling, and bias correction reasons.
    # 3.) If the input forcings haven't been opened and read into memory,
    #     open them.
    # 4.) Check to see if the ESMF objects for input forcings have been
    #     created. If not, create them, including the regridding object.
    # 5.) Regrid forcing grids for input cycle dates surrounding the
    #     current output timestep if they haven't been regridded.
    # 6.) Perform bias correction and/or downscaling.
    # 7.) Output final grids to LDASIN NetCDF files with associated
    #     WRF-Hydro geospatial metadata to the final output directories.
    # Throughout this entire process, log progress being made into LOG
    # files. Once a forecast cycle is complete, we will touch an empty
    # 'WrfHydroForcing.COMPLETE' flag in the directory. This will be
    # checked upon the beginning of this program to see if we
    # need to process any files.

    print('Forecast Cycle Length is: ' + str(ConfigOptions.cycle_length_minutes))
    for fcstCycleNum in range(ConfigOptions.nFcsts):
        ConfigOptions.current_fcst_cycle = ConfigOptions.b_date_proc + \
                                           datetime.timedelta(
            seconds=ConfigOptions.fcst_freq*60*fcstCycleNum
        )
        print('XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX')
        print('XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX')
        print('Processing Forecast Cycle: ' + ConfigOptions.current_fcst_cycle.strftime('%Y-%m-%d %H:%M'))
        fcstCycleOutDir = ConfigOptions.output_dir + "/" + \
            ConfigOptions.current_fcst_cycle.strftime('%Y%m%d%H%M')
        completeFlag = fcstCycleOutDir + "/WrfHydroForcing.COMPLETE"
        if os.path.isfile(completeFlag):
            # We have already completed processing this cycle,
            # move on.
            continue

        # If the cycle directory doesn't exist, create it.
        if not os.path.isdir(fcstCycleOutDir):
            try:
                os.mkdir(fcstCycleOutDir)
            except:
                ConfigOptions.errMsg = "Unable to create output " \
                                       "directory: " + fcstCycleOutDir
                errMod.err_out_screen(ConfigOptions.errMsg)

        # Compose a path to a log file, which will contain information
        # about this forecast cycle.
        ConfigOptions.logFile = fcstCycleOutDir + "/LOG_" + \
            ConfigOptions.d_program_init.strftime('%Y%m%d%H%M') + \
            "_" + ConfigOptions.current_fcst_cycle.strftime('%Y%m%d%H%M')

        # Initialize the log file.
        try:
            errMod.init_log(ConfigOptions)
        except:
            errMod.err_out_screen(ConfigOptions.errMsg)

        # Loop through each output timestep. Perform the following functions:
        # 1.) Calculate all necessary input files per user options.
        # 2.) Read in input forcings from GRIB/NetCDF files.
        # 3.) Regrid the forcings, and temporally interpolate.
        # 4.) Downscale.
        # 5.) Layer, and output as necessary.
        for outStep in range(1,ConfigOptions.num_output_steps+1):
            dOutput = ConfigOptions.current_fcst_cycle + datetime.timedelta(
                seconds=ConfigOptions.output_freq*60*outStep
            )
            print('=========================================')
            print("Processing for output timestep: " + dOutput.strftime('%Y-%m-%d %H:%M'))

            # Loop over each of the input forcings specifed.
            for forceKey in ConfigOptions.input_forcings:
                inputForcingMod[forceKey].calc_neighbor_files(ConfigOptions, dOutput)
                print('Previous GFS File = ' + inputForcingMod[forceKey].file_in1)
                print('Next GFS File = ' + inputForcingMod[forceKey].file_in2)
                #try:
                #    inputForcingMod[forceKey].calc_neighbor_files(ConfigOptions,dOutput)
                #except:
                #    errMod.err_out(ConfigOptions)


        # Close the log file.
        try:
            errMod.close_log(ConfigOptions)
        except:
            errMod.err_out_screen(ConfigOptions.errMsg)

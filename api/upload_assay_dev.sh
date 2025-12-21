#!/bin/bash

python scripts/upload_manual.py ../3_TestFattyAcids/config_3.json \
                                ../4_MoreIterations/config_4.json \
                                ../5_More_Iterations/config_5.json \
                                ../6_More_iterationns/config_6.json \
                                ../7_Moreiterations/config_7.json \
                                ../8_MoIterations/config_8.json \
                                ../9_Almost_there/config_9.json \
                                ../11_Validation/config_11.json \
                                ../12_ThermoPlateCompare/config_12.json \
                                ../13_TitrationValidationPilot/config_13.json \
                                ../14_DMSO_dilutionScheme/config_14.json \
                                ../22_validation2/config_22.json

python scripts/upload_echo.py  \
                    ../15_Echo/config_15.json \
                    ../16_Echo/config_16.json \
                    ../17_Buffers/config_17.json \
                    ../18_BuffersNCompounds/config_18.json \
                    ../19_Validation/config_19.json \
                    ../20_SpinShift/config_20.json \
                    ../21_SpinShift2/config_21json

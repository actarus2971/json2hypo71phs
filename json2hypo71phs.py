##################################################################
##################################################################
##################################################################
##################################################################

### IMPORTING LIBRARIES
import os,argparse,subprocess,copy,pwd,socket,time
import sys
import math
import decimal
import json
from six.moves import urllib
from datetime import datetime
import pandas

## the imports of Obspy are all for version 1.1 and greater
from obspy import UTCDateTime
#from obspy.core.event import Catalog, Event, Magnitude, Origin, Arrival, Pick
#from obspy.core.event import ResourceIdentifier, CreationInfo, WaveformStreamID
#try:
#    from obspy.core.event import read_events
#except:
#    from obspy.core.event import readEvents as read_events

class MyParser(argparse.ArgumentParser):
    def error(self, message):
        sys.stderr.write('error: %s\n' % message)
        self.print_help()
        sys.exit(2)

def parseArguments():
        parser=MyParser()
        parser.add_argument('--jsonin', help='Full path to json event file')
        parser.add_argument('--originid', help='INGV event id')
        parser.add_argument('--version', default='preferred',help="Agency coding origin version type (default: %(default)s)\n preferred,all, or an integer for known version numbers")
        parser.add_argument('--conf', default='./ws_agency_route.conf', help="needed with --originid\n agency webservices routes list type (default: %(default)s)")
        parser.add_argument('--agency', default='ingv', help="needed with --originid\n agency to query for (see routes list in .conf file) type (default: %(default)s)")
        if len(sys.argv) <= 1:
            parser.print_help()
            sys.exit(1)
        args=parser.parse_args()
        return args
# Nota: per aggiungere scelte fisse non modificabili usa choices=["known_version_number","preferred","all"]

try:
    import ConfigParser as cp
    #sys.stderr.write("ConfigParser loaded\n")
except ImportError:
    #sys.stderr.write("configparser loaded\n")
    import configparser as cp

# Build a dictionary from config file section
def get_config_dictionary(cfg, section):
    dict1 = {}
    options = cfg.options(section)
    for option in options:
        try:
            dict1[option] = cfg.get(section, option)
            if dict1[option] == -1:
                print("skip: %s" % option)
        except:
            print("exception on %s!" % option)
            dict1[option] = None
    return dict1


# JSON ENCODER CLASS
class DataEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            return float(o)

        if isinstance(o, datetime):
            return o.isoformat()

        return json.JSONEncoder.default(self, o)

def json_data_structure():
    null="null"
    event = {"data": {"event": {
            "id_locator": 0,
            "type_event": null,
            "provenance_name": null,
            "provenance_instance": null,
            "provenance_softwarename": self_software,
            "provenance_username": null,
            "provenance_hostname": null,
            "provenance_description": url_to_description,
            "hypocenters": []}}}
    hypocenter = {
            "ot": null,
            "lat": null,
            "lon": null,
            "depth": null,
            "err_ot": null,
            "err_lat": null,
            "err_lon": null,
            "err_depth": null,
            "err_h": null,
            "err_z": null,
            "confidence_lev": null,
            "e0_az": null,
            "e0_dip": null, 
            "e0": null,
            "e1_az": null,
            "e1_dip": null,
            "e1": null,
            "e2_az": null,
            "e2_dip": null,
            "e2": null,
            "fix_depth": null,
            "min_distance": null,
            "max_distance": null,
            "azim_gap": null,
            "sec_azim_gap": null,
            "rms": null,
            "w_rms": null,
            "is_centroid": null,
            "nph": null,
            "nph_s": null,
            "nph_tot": null,
            "nph_fm": null,
            "quality": null,
            "type_hypocenter": "",
            "model": null,
            "loc_program": null,
            "provenance_name": null,
            "provenance_instance": null,
            "provenance_softwarename": self_software,
            "provenance_username": null,
            "provenance_hostname": null,
            "provenance_description": url_to_description,
            "magnitudes": [],
            "phases": []
        }
    magnitude = {
              "mag": null,
              "type_magnitude": null,
              "err": null,
              "mag_quality": null, #?
              "quality": null, #?
              "nsta_used": null,
              # From StationsMag or Amplitude
              "nsta": null,
              "ncha": null,
              # From Boh
              "min_dist": null,
              "azimut": null,
              "provenance_name": null,
              "provenance_instance": null,
              "provenance_softwarename": self_software,
              "provenance_username": null,
              "provenance_hostname": null,
              "provenance_description": url_to_description,
              "amplitudes": []
            }

    amplitude = {
                  "time1": null,
                  "amp1": null,
                  "period1": null,
                  "time2": null,
                  "amp2": null,
                  "period2": null,
                  "type_amplitude": null,
                  "mag": null,
                  "type_magnitude": null,
                  "scnl_net": null,
                  "scnl_sta": null,
                  "scnl_cha": null,
                  "scnl_loc": null, 
                  #"ep_distance": 694,
                  #"hyp_distance": 0, ??
                  # "azimut": 161, ??
                  # "err_mag": 0,
                  # "mag_correction": 0,
                  "is_used": null,
                  "provenance_name": null,
                  "provenance_instance": null,
                  "provenance_softwarename": self_software,
                  "provenance_username": null,
                  "provenance_hostname": null,
                  "provenance_description": url_to_description
                }

    phase = {
              "isc_code": null,
              "weight_picker": null,
              "arrival_time": null,
              "err_arrival_time": null,
              "firstmotion": null,
              "emersio": null,
              "pamp": null,
              "scnl_net": null,
              "scnl_sta": null,
              "scnl_cha": null,
              "scnl_loc": null,
              "ep_distance": null,
              "hyp_distance": null,
              "azimut": 140,
              "take_off": 119,
              "polarity_is_used": null,
              "arr_time_is_used": null,
              "residual": -0.12,
              "teo_travel_time": null,
              "weight_phase_a_priori": null,
              "weight_phase_localization": null,
              "std_error": null,
              "provenance_name": "INGV",
              "provenance_instance": "BULLETIN-INGV",
              "provenance_softwarename": self_software,
              "provenance_username": null,
              "provenance_hostname": null,
              "provenance_description": url_to_description
            }
    return event,hypocenter,magnitude,amplitude,phase
    
# Get the json file from the caravel webservice
def getjson(origin_id,bu,op):
    urltext=bu + "?originid=" + str(origin_id) + op
    try:
        req = urllib.request.Request(url=urltext)
        try:
            res = urllib.request.urlopen(req)
        except Exception as e:
            print("Query in urlopen")
            if sys.version_info[0] >= 3:
               print(e.read()) 
            else:
               print(str(e))
            sys.exit(1)
    except Exception as e:
        print("Query in Request")
        print(e.read()) 
        sys.exit(1)
    return res.read().decode('utf-8','replace'),urltext

#################### END OF QML PARSER COMMON PART ###########################
###### FROM HERE ON ADD ON PURPOSE OUTPUT FORMATTERS #########################

############# HYPO71 PHASE FILE ##############################################
# Back Conversions are taken from https://gitlab.rm.ingv.it/adsdbs/seisev/blob/master/startingpoint/1_0_1/skeleton.sql#L15628 
def convert_sispick_quality(q):
    qf=float(q)
    if qf <= 0.1:
        w='0'
    elif qf > 0.1 and qf <= 0.3:
        w='1'
    elif qf > 0.3 and qf <= 0.6:
        w='2'
    elif qf > 0.6 and qf <= 1.0:
        w='3'
    elif qf > 1.0 and qf <= 3.0:
        w='4'
    elif qf > 3.0:
        w='8'
    return w

def polarity_qml2hypo(qpp):
    if qpp == "positive":
       p='U'
    elif qpp == "negative":
       p='D'
    elif qpp == "undecidable":
       p=''
    return p


def onset_qml2hypo(qpo):
    if qpo == "impulsive":
       o = 'i'
    elif qpo == "emergent":
       o = 'e'
    elif qpo == "questionable":
       o = ''
    return o

def set_format(a,p):
    if a < 10:
         af="%3.1f" 
    elif a >= 10 and a < 100:
         af="%3.0f"
    elif a >= 100 and a < 1000:
         af="%3i"
    if p < 10:
         pf="%3.1f" 
    elif p >= 10 and p < 100:
         pf="%3.0f"
    elif p >= 100 and p < 1000:
         pf="%3i"
    return af,pf

def to_hypoinverse(pP,pS,a,eid,oid,ver):
    # https://escweb.wr.usgs.gov/content/software/HYPOINVERSE/doc/hyp1.40.pdf
    # ftp://ehzftp.wr.usgs.gov/klein/hyp1.41/hyp1.41-release-notes.pdf (updated 2015)
    # The output format described in the above pdf is the classical hypo71 phase file implemented in hypoinverse with additional information
    phs=[]
    for k,v in pP.items():
        hi_line = "x" * 110
        p_used= v[7]
        p_tim = UTCDateTime(v[6])
        if p_used:
           pol=" " if v[4] == "null" or v[4] == "" else v[4]
           wei=" " if v[5] == "null" or v[5] == "" else v[5]
           if v[8] == "null" or v[8] == "":
              com=" "
              cha="---"
           else:
              com=v[8][2] if len(v[8]) == 3 else " "
              cha=v[8]
           Ptime="%2.2i%2.2i%2.2i%2.2i%2.2i%05.2f" % (int(str(p_tim.year)[2:4]),p_tim.month,p_tim.day,p_tim.hour,p_tim.minute,(float(p_tim.second) + float(p_tim.microsecond)/1000000.))
           if len(v[0]) == 4:
              hi_line = v[0] + "x" + v[3] + pol + wei + com + Ptime + hi_line[24:]
           elif len(v[0]) == 5:
              hi_line = v[0][0:4] + "x" + v[3] +  pol + wei + com + Ptime + hi_line[24:77] + v[0][4] + hi_line[78:]
           elif len(v[0]) == 3:
              hi_line = v[0] + "xx" + v[3] + pol + wei + com + Ptime + hi_line[24:]
           try:
               s_used = pS[k][7]
           except:
               s_used=False
               pass
           if s_used:
              s_tim = UTCDateTime(pS[k][6])
              s_seconds = float((int(s_tim.minute)-int(p_tim.minute))*60.) + float((float(s_tim.second)+float(s_tim.microsecond)/1000000.))
              fmt = "%05.2f" if s_seconds < 100 else "%05.1f" # if the S seconds are >= 100 the format is modified to keep alignment
              weis = " " if pS[k][5] == "null" or pS[k][5] == "" else pS[k][5]
              hi_line = hi_line[:31] + fmt % (s_seconds) + "x" + pS[k][3] + "x" + weis + hi_line[40:]
           hi_line = hi_line[:78] + cha + v[1] + v[2] + hi_line[85:]
           try:
              ka_n=k + "_" + v[8][0:2] + "N"
              ka_e=k + "_" + v[8][0:2] + "E"
              # The QML INGV AML channel Amplitude is half of peak to peak while hypo71/hypoinverse/hypoellipse is peak-to-peak so ...
              # here for clarity channel amp (here already in mm) is multiplied by 2 then the two channel peak-to-peak amps are summed 
              # and the mean is caculated to be written in f3.0 from column 43
              hi_amp= ((float(a[ka_n][4])*2 + float(a[ka_e][4])*2)/2) 
              # first I used one of the two periods, float(a[ka_n][4]), now the mean ... is it correct?
              hi_per= (float(a[ka_n][5]) + float(a[ka_e][5]))/2 
              amp_present=True
              fa,fp = set_format(hi_amp,hi_per)
              hi_line = hi_line[:44] + fa % (hi_amp) + fp % (hi_per) + hi_line[50:]
           except Exception as e:
              amp_present=False
              pass
           idlen=len(str(eid))
           oridlen=len(str(oid))
           verlen=len(str(ver))
           hi_line=hi_line.replace('x',' ')
           hi_line=hi_line[:89] + "EVID:" + str(eid) + ",ORID:" + str(oid) + ",V:" + str(ver)
           # For information completeness, 
           # both the peak-to-peak channel amplitudes are reported in free format at the end of the line
           try: 
               all_amps=[ v for k,v in a.items() if k.startswith(ka_n[:-3])]
           except:
               all_amps=[]
           if len(all_amps) > 0:
              for la in all_amps:
                  hi_line=hi_line + "," + str(la[3]) + ":" + str(float(la[4])*2)
              #hi_line=hi_line + ",AN:" + str(float(a[ka_n][4])*2) + ",AE:" + str(float(a[ka_e][4])*2)
           
           phs.append(hi_line)
           #hi_file_out.write(hi_line)
    if len(phs) != 0:
       phs.append('') # Terminator line for free 1st trial location
    return phs 
    #hi_file_out.close() 
#Start Fortran
#Col. Len. Format Data
#1 4 A4 4-letter station site code. Also see col 78.
#5 2 A2 P remark such as "IP". If blank, any P time is ignored.
#7 1 A1 P first motion such as U, D, +, -, C, D.
#8 1 I1 Assigned P weight code.
#9 1 A1 Optional 1-letter station component.
#10 10 5I2 Year, month, day, hour and minute.
#20 5 F5.2 Second of P arrival.
#25 1 1X Presently unused.
#26 6 6X Reserved remark field. This field is not copied to output files.
#32 5 F5.2 Second of S arrival. The S time will be used if this field is nonblank.
#37 2 A2, 1X S remark such as "ES".
#40 1 I1 Assigned weight code for S.
#41 1 A1, 3X Data source code. This is copied to the archive output.
#45 3 F3.0 Peak-to-peak amplitude in mm on Develocorder viewer screen or paper record.
#48 3 F3.2 Optional period in seconds of amplitude read on the seismogram. If blank, use the standard period from station file.
#51 1 I1 Amplitude magnitude weight code. Same codes as P & S.
#52 3 3X Amplitude magnitude remark (presently unused).
#55 4 I4 Optional event sequence or ID number. This number may bereplaced by an ID number on the terminator line.
#59 4 F4.1 Optional calibration factor to use for amplitude magnitudes. If blank, the standard cal factor from the station file is used.
#63 3 A3 Optional event remark. Certain event remarks are translated into 1-letter codes to save in output.
#66 5 F5.2 Clock correction to be added to both P and S times.
#71 1 A1 Station seismogram remark. Unused except as a label on output.
#72 4 F4.0 Coda duration in seconds.
#76 1 I1 Duration magnitude weight code. Same codes as P & S.
#77 1 1X Reserved.
#78 1 A1 Optional 5th letter of station site code.
#79 3 A3 Station component code.
#82 2 A2 Station network code.
#84-85 2 A2 2-letter station location code (component extension)

    #print('#### Not Used Picks ############')
    #for k,v in pick_P.items():
    #    p_not_used=True if v[-1] == '0' else False
    #    if p_not_used:
    #       print(v)
    #       try:
    #           s_not_used=True if pick_S[k][-1] == '0' else False
    #       except:
    #           s_not_used=False
    #           pass
    #       if s_used:
    #          print(pick_S[k])
           #if s_used == '1':
#    print(linea['PLONS_P_1'])
#    if len(linea['PLONS_P_1'][0]) > 4:
#       fase = str(linea['PLONS_P_1'][0][0:4])
#    print(type(fase),fase)

################## MAIN ####################
args=parseArguments()

# Getting this code name
self_software=sys.argv[0]

# If a qml input file is given, file_qml is the full or relative path_to_file
if args.jsonin:
   response=args.jsonin
   url_to_description = "File converted from json file " + args.jsonin.split(os.sep)[-1]

# This is the version that will be retrieved from the qml
orig_ver=int(args.version)

if not args.jsonin and not args.originid:
       print("Either --jsonin or --originid are needed")
       sys.exit()

# If jsonin is not given and an originid is given, file_json is the answer from a query and the configuration file is needed
if args.originid:
   oid=args.originid
   # Now loading the configuration file
   if os.path.exists(args.conf) and os.path.getsize(args.conf) > 0:
      paramfile=args.conf
   else:
      print("Config file " + args.conf + " not existing or empty")
      sys.exit(2)
   confObj = cp.ConfigParser()
   confObj.read(paramfile)
   # Metadata configuration
   agency_name = args.agency.lower()
   try:
       ws_route = get_config_dictionary(confObj, agency_name)
   except Exception as e:
       print(e) 
       sys.exit(1)
   # Now requesting the qml file from the webservice
   response, url_to_description = getjson(oid,ws_route['base_url'],ws_route['in_options'])
   if not response or len(response) == 0:
      print("Void answer with no error handling by the webservice")
      sys.exit(1)
   full_event = json.loads(response)
   for o in full_event['data']['event']['origins']:
       if o['type_origin']['version_name'] == 'bulletin fm' and o['type_origin']['version_value'] == orig_ver and o['provenance']['description'] == 'PFX interactive revision':
          origin_found=True
          origin=o
          break
       else:
          origin_found=False

########## FROM HERE THE PART OF MAIN HANDLING SPECIFICALLY TO OUTPUT HYPO71PHS
## This part should match the json FROM quakedb with the json strutcture and then the rest should work as the forked script

event,hypocenter,magnitude,amplitude,phase = json_data_structure()
EARTH_RADIUS=6371 # Defined after eventdb setup (valentino.lauciani@ingv.it)
DEGREE_TO_KM=111.1949 # Defined after eventdb setup (valentino.lauciani@ingv.it)

if origin_found:
    # Ottengo gli ID delle versioni preferite
    eid=full_event['data']['event']['id']
    id_localspace=full_event['data']['event']['id_localspace']
    event_group_id=full_event['data']['event']['event_group_id']
    preferred_origin_id=full_event['data']['event']['preferred_origin_id']
    preferred_magnitude_id=full_event['data']['event']['preferred_magnitude_id']
    type_event=full_event['data']['event']['type_event']
    localspace_name=full_event['data']['event']['localspace']['name']
    provenance_name_=full_event['data']['event']['provenance']['name']
    eo = copy.deepcopy(event) 
    eo["id_locator"] = id_localspace
    eo["type_event"] = type_event
    eo["provenance_name"] = provenance_name_
    eo["provenance_instance"] = localspace_name
    or_id_to_write=oid
    version_name=o['type_origin']['version_name'] 
    version_number=o['type_origin']['version_value']
    oo = copy.deepcopy(hypocenter)
    try:
        oo['ot'] = origin['ot']
    except:
        pass
    try:
        oo['lat'] = origin['lat']
    except:
        pass
    try:
        oo['lon'] = origin['lon']
    except:
        pass
    try:
        oo['depth'] = origin['depth']
    except:
        pass
    if origin['fix_depth']:
       oo['fix_depth'] = 1
    else:
       oo['fix_depth'] = 0
    # space time coordinates errors
    try:
        oo['err_ot']=origin['err_ot']
    except Exception as e:
        print(e)
        pass
    try:
        oo['err_lat']=(float(origin['err_lat_deg'])*(EARTH_RADIUS*2*math.pi))/360. # from degrees to km
    except Exception as e:
        print(e)
        pass
    try:
        oo['err_lon']=(float(origin['err_lon_deg'])*EARTH_RADIUS*math.cos(float(origin['lat'])*2*(math.pi/360.))*2*math.pi)/360. # from degrees to km
    except Exception as e:
        print(e)
        pass
    try:
        oo['err_depth']=float(origin['err_depth'])
    except Exception as e:
        print(e)
        pass
    try:
        oo['err_h'] = float(origin['err_h'])
    except Exception as e:
        print(e)
        pass
    try:
        oo['err_z'] = float(origin['err_z'])
    except Exception as e:
        print('err_z: ',e)
        pass
#   ######### i prossimi tre valori commentati sono legati in modo NON bidirezionale ai valori dell'ellissoide
#   #1 min_ho_un = origin['origin_uncertainty']['min_horizontal_uncertainty']
#   #2 max_ho_un = origin['origin_uncertainty']['max_horizontal_uncertainty']
#   #3 az_max_ho_un = origin['origin_uncertainty']['azimuth_max_horizontal_uncertainty']
#   #4 pref_desc = origin['origin_uncertainty']['preferred_description']
    try:
        oo['confidence_lev'] = origin['confidence_level']
    except Exception as e:
        print(e)
        pass
    try:
        oo['min_distance'] = origin['min_distance']
    except Exception as e:
        print(e)
        pass
    try:
        oo['med_distance'] = origin['med_distance']
    except Exception as e:
        print(e)
        pass
    try:
        oo['max_distance'] = origin['max_distance']
    except Exception as e:
        print(e)
        pass
    try:
        oo['azim_gap'] = origin['azim_gap']
    except Exception as e:
        print(e)
        pass
    try:
        oo['rms'] = origin['rms']
    except Exception as e:
        print(e)
        pass
    try:
        oo['w_rms'] = origin['w_rms']
    except Exception as e:
        print(e)
        pass
    try:
        oo['is_centroid'] = origin['is_centroid']
    except Exception as e:
        print(e)
        pass
    try:
        oo['model'] = origin['provenance']['model']
    except Exception as e:
        print(e)
        pass
    oo['provenance_name'] = origin['provenance']['name']
    oo['provenance_istance'] = origin['type_origin']['version_name']
    oo['quality'] = origin['quality']
    oo['quality_numeric'] = origin['quality_numeric']
    
    P_count_all=0
    S_count_all=0
    P_count_use=0
    S_count_use=0
    Pol_count=0
    pick_P = {}
    pick_S = {}
    for pick in origin['arrivals']:
        po = copy.deepcopy(phase)
        po['arr_time_is_used']=pick['arr_time_is_used']
        pick_id=pick['id']
        try:
            po['isc_code']      = pick['isc_code']
        except Exception as e:
            print(e)
            pass
        if po['isc_code'].lower()[0] == 'p':
           P_count_all += 1 
           if po['arr_time_is_used']:
              P_count_use += 1
        if po['isc_code'].lower()[0] == 's':
           S_count_all += 1 
           if po['arr_time_is_used']:
              S_count_use += 1
        try:
            po['scnl_net']      = pick['pick']['net']
        except Exception as e:
            print(e)
            pass
        try:
            po['scnl_sta']      = pick['pick']['sta']
        except Exception as e:
            print(e)
            pass
        try:
            po['scnl_cha']      = pick['pick']['cha']
        except Exception as e:
            print(e)
            pass
        try:
            po['scnl_loc'] = pick['pick']['loc']
        except Exception as e:
            print(e)
            pass
        try:
            po['arrival_time']  = pick['pick']['arrival_time']
        except Exception as e:
            print(e)
            pass
        low_unc=float(pick['pick']['lower_uncertainty']) if pick['pick']['lower_uncertainty'] else pick['pick']['lower_uncertainty']
        up_unc=float(pick['pick']['upper_uncertainty']) if pick['pick']['upper_uncertainty'] else pick['pick']['upper_uncertainty']
        if low_unc and up_unc:
            po['weight_picker'] = convert_sispick_quality((low_unc+up_unc))
            #print("Weight from uncertainties",po['weight_picker'])
        else:
            po['weight_picker'] = pick['pick']['quality_class']
            #print("Weight from file",po['weight_picker'])
        try:
            #po['firstmotion'] = polarity_qml2hypo(pick['polarity'])
            if pick['pick']['firstmotion']:
               Pol_count += 1
               po['firstmotion'] = pick['pick']['firstmotion']
               #print("polarity nr ",Pol_count,po['firstmotion'])
        except Exception as e:
            print(e)
            pass
        try:
            #po['emersio'] = onset_qml2hypo(pick['onset'])
            if pick['pick']['emersio']:
               po['emersio'] = pick['pick']
        except Exception as e:
            print(e)
            pass
        try:
            po['ep_distance_km']   = pick['ep_distance_km']
        except:
            po['ep_distance_delta']   = pick['ep_distance_delta']
        try:
            po['azimut']        = pick['azimut']
        except:
            pass
        try:
            po['take_off']      = pick['take_off']
        except:
            pass
        try:
            po['weight_phase_localization'] = pick['weight']
        except:
            pass
        try:
            po['residual'] = pick['residual']
        except:
            pass
        # Writing the Pick into the picks dictionary based on the sta and net key (for reuse in formatting steps)
        if po['arr_time_is_used'] == 1:
           pick_key= str(po['scnl_net']) + "_" + str(po['scnl_sta'])
           if str(po['isc_code']).lower() == 'p':
              pick_P[str(pick_key)] = [str(po['scnl_sta']),str(po['scnl_net']),str(po['scnl_loc']),str(po['isc_code']),str(po['firstmotion']),str(po['weight_picker']),str(po['arrival_time']),str(po['arr_time_is_used']),str(po['scnl_cha'])]
           if str(po['isc_code']).lower() == 's':
              pick_S[str(pick_key)] = [str(po['scnl_sta']),str(po['scnl_net']),str(po['scnl_loc']),str(po['isc_code']),str(po['firstmotion']),str(po['weight_picker']),str(po['arrival_time']),str(po['arr_time_is_used']),str(po['scnl_cha'])]
    oo["phases"].append(po)
    oo['nph'] = P_count_use+S_count_use
    oo['nph_s'] = S_count_use
    oo['nph_tot'] = P_count_all+S_count_all
    oo['nph_fm'] = Pol_count
    for mag in origin['magnitudes']:
        mm = copy.deepcopy(magnitude)
        mm['mag'] = mag['mag']
        mm['type_magnitude'] = mag['type_magnitude']
        mm['err'] = (float(mag['lower_uncertainty'])+float(mag['upper_uncertainty']))/2
        mm['nsta_used'] = mag['nsta_used']
        mm['provenance_name'] = mag['provenance']['name']
        mm['provenance_instance'] = mag['localspace']['name']
        amps={}
        for sta_mag in mag['stationmagnitudes']:
            am = copy.deepcopy(amplitude)
            am['type_magnitude'] = sta_mag['type_magnitude']
            am['mag'] = sta_mag['mag']
            am['is_used'] = 1 if sta_mag['is_used'] else 0
            if sta_mag['amplitude']['type_amplitude']['unit'] == 'm':
               a_mul=1000.
            else:
               a_mul=1.
            am['time1'] = sta_mag['amplitude']['time1']
            am['amp1'] = sta_mag['amplitude']['amp1']
            am['period1'] = sta_mag['amplitude']['period']
            am['time2'] = sta_mag['amplitude']['time1']
            am['amp2'] = sta_mag['amplitude']['amp1']
            am['period'] = sta_mag['amplitude']['period']
            am['type_amplitude'] = sta_mag['amplitude']['type_amplitude']['name']
            am['scnl_net'] = sta_mag['amplitude']['net']
            am['scnl_sta'] = sta_mag['amplitude']['sta']
            am['scnl_cha'] = sta_mag['amplitude']['cha']
            am['scnl_loc'] = sta_mag['amplitude']['loc']
            am['provenance_name'] = sta_mag['amplitude']['provenance']['name']
            am['provenance_instance'] = sta_mag['amplitude']['localspace']['name']
            am['provenance_software'] = sta_mag['amplitude']['provenance']['program']
            am['evalueation_mode'] = sta_mag['amplitude']['provenance']['evaluationmode']
            amps_key= str(am['scnl_net']) + "_" + str(am['scnl_sta']) + "_" + str(am['scnl_cha'])
            half_pp_amp_mm = ((abs(float(am['amp1']))+abs(float(am['amp2'])))/2)*a_mul
            amps[str(amps_key)] = [str(am['scnl_sta']),str(am['scnl_net']),str(am['scnl_loc']),str(am['scnl_cha']),str(half_pp_amp_mm),str(am['period'])]
            mm["amplitudes"].append(am)
        oo["magnitudes"].append(mm)
    eo["data"]["event"]["hypocenters"].append(oo) # push oggetto oo in hypocenters
if not origin_found:
   sys.stderr.write("Chosen version doesnt match any origin id")
   sys.exit(202) # Il codice 202 e' stato scelto per identificare il caso in cui tutto sia corretto ma non ci sia alcuna versione come quella scelta
out_print=to_hypoinverse(pick_P,pick_S,amps,eid,or_id_to_write,version_number)
for item in out_print:
    print(item)
sys.exit(0)

###################################################################################
# Author : Sabry Elsayed 
# Data   : 25 /3 / 2024
############################### Laser HIL Test #####################################                    
#
#
####################################################################################


import  serial,time

import sys
import struct


LR_CONTINOUS_MODE_STAT = False

LR_TARGET_TYPE_RESPONSE    = [0xEE ,0x16 ,0x02 ,0x03 ,0x03 ,0x06]
LR_CONTINOUS_MODE_RESPONSE = [0XEE ,0x16 ,0x06 ,0x03 ,0x04 ,0x04 ,0x00 ,0x00 ,0x00 ,0x0B]
LR_NOT_DATA_FRAME_CMD = [0XEE ,0x16 ,0x06 ,0x03 ,0x05 ,0x04 ,0x00 ,0x00 ,0x00 ,0x0C]
LR_WRONG_RESPONSE_FRAME = [0XEE ,0x16 ,0x06 ,0x03 ,0x04 ,0x04 ,0x00 ,0x00 ,0x00 ,0x0A]
'''
 To indicate to constant bytes of the laser commands
  that is the same at all commands
'''
LR_HEADER_HIGH  = 0xEE
LR_HEADER_LOW   = 0x16
LR_EQ_CODE      = 0x03


'''
To indicate to the indices of command information or response 
'''
HEAD_H_IND   =   0
HEAD_L_IND   =   1
LEN_IND      =   2
EQ_CODE_IND  =   3
CMD_IND      =   4

'''
Commands 
'''
SET_TARGET_TYPE_CMD    = 0x03
SET_CONTINOUS_RANGING  = 0x04
LR_ID  = 0x04
LR_DATA_CMD = 0x01


# ######################## Configure Serial Paramters #########################
uart_serial = serial.Serial('COM3', 9600, 8, 'N', 1) # open serial connection
can_serial =  serial.Serial('COM5', 115200, 8, 'N', 1) # open serial connection
# #############################################################################
# print("sum = " , val)

#########################################################################
def WriteDataToSerialPort(Data):     
            uart_serial.write(serial.to_bytes(Data))                #(uart_serial.to_bytes(Data))
##########################################################################            


############################## Read Serial ###################################### 
def Read_Serial_Port(serial_type,Data_Len):
    Serial_Value = serial_type.read(Data_Len)
    Serial_Value_len = len(Serial_Value)
    while Serial_Value_len <= 0:
        Serial_Value = serial_type.read(Data_Len)
        Serial_Value_len = len(Serial_Value)
    return Serial_Value         
    # return Serial_Value
########################################################################################

########################### Calculate CheckSum ###########################################
def calc_cs(data):
    checksum = 0
    for byte in data:
        if isinstance(byte, str):
            try:
                checksum += int(byte, 16)  # Convert hexadecimal string to integer
            except ValueError:
                pass  # Ignore non-convertible elements
        else:
            checksum += byte  # If it's not a string, assume it's already an integer
    checksum %= 256
    return checksum     
##########################################################################################

################################## Validate Command ######################################    
def check_cmd(cmd_info) :
     cs_data = cmd_info[3:-1]
     cs = calc_cs(cs_data)
     rec_cs = int(cmd_info[-1] , 16)
     if cs == rec_cs:
          return True
     else:
          return False
##########################################################################################     

################################## To Receive Command #####################################
def Reveive_CMD():
     Serial_Value = Read_Serial_Port(uart_serial,2)
     if Serial_Value[0] == LR_HEADER_HIGH and Serial_Value[1] == LR_HEADER_LOW: 
           data_len = Read_Serial_Port(uart_serial,1)
           cmd_info = Read_Serial_Port(uart_serial,data_len[0])
           rec_cs = calc_cs(cmd_info)
           cmd_cs   = Read_Serial_Port(uart_serial,1) 
        #    retVal = hex([Serial_Value , data_len , cmd_info , cmd_cs])   
           retVal = [hex(item) for sublist in [Serial_Value, data_len, cmd_info, cmd_cs] for item in sublist]
           return retVal
     return None
        #    if check_cmd(cmd_cs[0] , rec_cs):


#################################Parse Command ###########################################    
def LR_ParseCMD(cmd_info):
     global LR_CONTINOUS_MODE_STAT  
    #  print(type(int(cmd_info[CMD_IND])) , type(SET_TARGET_TYPE_CMD))
     if   int(cmd_info[CMD_IND], 16) == SET_TARGET_TYPE_CMD:
          print("Multiple Targrt mode was set")
          WriteDataToSerialPort(bytearray(LR_TARGET_TYPE_RESPONSE))
     elif int(cmd_info[CMD_IND], 16) == SET_CONTINOUS_RANGING: 
          print("continous mode was set")
          WriteDataToSerialPort(bytearray(LR_CONTINOUS_MODE_RESPONSE))
          LR_CONTINOUS_MODE_STAT = True 
             
          
          

############################## Process Laser Command ####################################
def LR_Process_CMD():
     LR_Request = Reveive_CMD()
     print(LR_Request)
     if check_cmd(LR_Request):
          LR_ParseCMD(LR_Request)
          return True
     else:
          return False     
     
#################################################Resceive Response ############################################################
def LR_ReceiveResponse():
    # Serial_Value = Read_Serial_Port(can_serial,1)
    sequence = Read_Serial_Port(can_serial,1)
    LR_CMD  = Read_Serial_Port(can_serial ,1)
    if LR_CMD[0] == 0x01: 
     #    print("is data frame ")
        distance_h = Read_Serial_Port(can_serial ,1)
        distance_l = Read_Serial_Port(can_serial ,1)
        typeOftarget = Read_Serial_Port(can_serial ,1)
        noOfTarget = Read_Serial_Port(can_serial ,1)
        timestamp_l = Read_Serial_Port(can_serial ,1)
        timestamp_h = Read_Serial_Port(can_serial ,1)
    #    retVal = hex([Serial_Value , data_len , cmd_info , cmd_cs])   
        retVal = [hex(item) for sublist in [sequence, LR_CMD, distance_h,distance_l,typeOftarget,noOfTarget,timestamp_l,timestamp_h] for item in sublist]
        return retVal
    elif LR_CMD[0] == 0x00: 
          ErrCode = Read_Serial_Port(can_serial ,1)
          timestamp_l = Read_Serial_Port(can_serial ,1)
          timestamp_h = Read_Serial_Port(can_serial ,1)
          dumy_1 = Read_Serial_Port(can_serial ,1)
          dumy_2 = Read_Serial_Port(can_serial ,1)
          dumy_3 = Read_Serial_Port(can_serial ,1)
        

          # print("is error frame ")
          retVal = [hex(item) for sublist in [sequence, LR_CMD, ErrCode,timestamp_l,timestamp_h,dumy_1,dumy_2,dumy_3] for item in sublist]
          return retVal
    return None
##################################################################################################################################################

################################################ Check Response ##################################################################################

def check_response(actual_response , expected_response):
     if actual_response == expected_response :
          return True
     else:
          return False
##################################################################################################################################################


############################################## Open test results file ############################################################################
with open('test_results.txt', 'w') as file:
     file.write("***************************************************************************************************\n")
     file.write("***********************************/Laser Test Report/*********************************************\n")
     file.write("***************************************************************************************************\n")
     file.write("Laser Test case 1 : ")
###################################################################################################################################################





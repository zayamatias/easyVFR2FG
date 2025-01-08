import socket
import csv
import math
import time


SEQUENCE = 60
FRAMETIME = 1/SEQUENCE
HOST = "127.0.0.1"  # Replace with the target IP address if needed
PORT = 49003

def shortest_heading_path(hdg1, hdg2):
    """
    Calculate the shortest angular distance between two headings.

    Args:
        hdg1 (float): The first heading (in degrees).
        hdg2 (float): The second heading (in degrees).

    Returns:
        float: The shortest angular distance (in degrees), which is always non-negative.
               It also indicates direction: positive means clockwise, negative means counterclockwise.
    """
    # Normalize headings to [0, 360)
    hdg1 %= 360
    hdg2 %= 360

    # Calculate angular difference
    diff = hdg2 - hdg1

    # Adjust to the shortest path
    if diff > 180:
        diff -= 360
    elif diff < -180:
        diff += 360

    return diff

def calculate_bank_angle(ground_speed, heading_change_deg):
    """
    Calculate the approximate bank angle of an airplane during a turn.

    Parameters:
        ground_speed (float): Ground speed in m/s.
        heading_change_deg (float): Heading change in degrees over one second.

    Returns:
        float: Bank angle in degrees.
    """
    # Convert heading change from degrees to radians
    heading_change_rad = math.radians(heading_change_deg)


    # Calculate the turn rate (omega) in radians/second
    turn_rate = heading_change_rad / 1  # Since interval is 1 second

    # Calculate the turn radius (R) in meters
    if turn_rate != 0 and ground_speed != 0:
        turn_radius = ground_speed / turn_rate
    else:
        return 0.0  # No turn, so bank angle is 0

    # Calculate the bank angle in radians using the formula
    g = 9.81  # Gravity acceleration in m/s^2
    bank_angle_rad = math.atan((ground_speed ** 2) / (g * turn_radius))

    # Convert the bank angle to degrees
    bank_angle_deg = math.degrees(bank_angle_rad)

    return bank_angle_deg

def calculate_pitch_angle(height1, height2, ground_speed):
    """
    Calculate the pitch angle based on the change in altitude and ground speed.

    Args:
        height1 (float): Initial altitude.
        height2 (float): Final altitude.
        ground_speed (float): Ground speed.

    Returns:
        float: Pitch angle in degrees.
    """
    # Calculate the change in altitude
    altitude_change = height2 - height1

    # Calculate the flight path angle (pitch) in radians
    if ground_speed != 0 and altitude_change!=0:
        pitch_angle_rad = math.atan(altitude_change / ground_speed)
    else:
        return 0.0  # No horizontal movement, so pitch angle is 0

    # Convert the pitch angle to degrees
    pitch_angle_deg = math.degrees(pitch_angle_rad)

    return pitch_angle_deg

def send_udp_data(message):
    """
    Send a message via UDP.

    Args:
        message (str): The message to send.
    """
    # Define the target host and port

    try:
        # Create a UDP socket
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # Convert the message to bytes (UDP requires data to be in bytes)
        byte_message = message.encode('utf-8')

        # Send the message
        
        start_time = time.time()
        udp_socket.sendto(byte_message, (HOST, PORT))
        while time.time() - start_time < FRAMETIME:
            pass
        print (f'SENT {message}')
    except Exception as e:
        print(f"An error occurred: {e}")

    finally:
        # Close the socket
        udp_socket.close()

def convert(myrows):
    """
    Convert rows of data and send them via UDP.

    Args:
        myrows (list): List of rows to convert.
    """
    values = bytearray()
    extracts = [['%03.10f', 8, 4], ['%03.10f', 8, 5], ['%03.2f', 4, 6], ['%03.2f', 4, 7], ['%05.2f', 8, 8], ['%05.2f', 4, 10], ['%03.2f', 4, 22], ['%03.2f', 4, 23], ['%03.2f', 8, 24], ['%03.2f', 4, 25], ['%03.2f', 4, 27], ['%05.2f', 4, -1]]
    oldvalues = [0] * 13
    rowvalues = [0] * 12
    rowread = 0
    bank_angle = 0
    pitch_angle = 0
    oldbankangle = 0
    oldpitchangle = 0
    device_type=0
    for row_num, myrow in enumerate(myrows, start=1):
        print (row_num)
        if row_num==1:
            device_type=myrow[1]
        if myrow[1]!=device_type:
            continue
        try:
            retrow = ''
            idx = 0
            for extract in extracts:
                col = extract[2]
                if col == -1:
                    rowvalues[idx] = float(myrow[8]) - float(myrow[10])
                else:
                    rowvalues[idx] = float(myrow[extract[2]])
                if rowvalues[idx] == 999:
                    rowvalues[idx] = 0.0
                idx += 1

            if rowvalues[3] != oldvalues[3]:
                diff = shortest_heading_path(oldvalues[3], rowvalues[3])
                bank_angle = calculate_bank_angle(rowvalues[2], diff)
            else:
                bank_angle = oldbankangle
            if rowvalues[4] != oldvalues[4]:
                pitch_angle = calculate_pitch_angle(oldvalues[4], rowvalues[4], rowvalues[2])
            else:
                pitch_angle = oldpitchangle
            if rowread != 0:
                for ts in range(1, SEQUENCE):
                    retrow = ''
                    for i in range(0, 12):
                        if i == 8:
                            step = (bank_angle - oldbankangle) / SEQUENCE
                            nv = oldbankangle + (step * ts)
                            retrow += str(extracts[i][0] % nv) + '\t'
                            continue
                        if i == 3:
                            diff = shortest_heading_path(oldvalues[i], rowvalues[i])
                            step = diff / SEQUENCE
                            nv = oldvalues[i] + (step * ts)
                            if nv > 360:
                                nv -= 360
                            if nv < 0:
                                nv += 360
                            retrow += str(extracts[i][0] % nv) + '\t'
                            continue
                        if i == 6:
                            step = (pitch_angle - oldpitchangle) / SEQUENCE
                            nv = oldpitchangle + (step * ts)
                            retrow += str(extracts[i][0] % nv) + '\t'
                            continue
                        step = (rowvalues[i] - oldvalues[i]) / SEQUENCE
                        nv = oldvalues[i] + (step * ts)
                        retrow += str(extracts[i][0] % nv) + '\t'
                    retrow = retrow[:-1] + '\n'
                    send_udp_data(retrow)
                oldbankangle = bank_angle
                oldpitchangle = pitch_angle
            rowread = 1
            retrow = ''
            for i in range(0, 12):
                if i == 8:
                    retrow += str(extracts[i][0] % bank_angle) + '\t'
                    continue
                if i == 6:
                    retrow += str(extracts[i][0] % pitch_angle) + '\t'
                    continue
                retrow += str(extracts[i][0] % rowvalues[i]) + '\t'
            oldvalues = rowvalues.copy()
            retrow = retrow[:-1] + '\n'
            send_udp_data(retrow)
        except Exception as e:
            print(f"Error parsing value at index {row_num}: {e}")
    return values

def parse_csv(file_path):
    """
    Parses the given CSV file and prints its contents row by row.

    Args:
        file_path (str): Path to the CSV file.
    """
    try:
        with open(file_path, mode='r', encoding='utf-8') as file:
            csv_reader = csv.reader(file)
            headers = next(csv_reader, None)  # Read the header row, if any

            if headers:
                print("Headers:", headers)
            else:
                print("No headers found in the CSV file.")

            print("\nRows:")
            thebytes = b''
            thebytes = convert(csv_reader)

    except FileNotFoundError:
        print(f"Error: The file '{file_path}' does not exist.")
    except Exception as e:
        print(f"An error occurred: {e}")

    return thebytes

if __name__ == '__main__':
    csv_file = "lepp-leso.csv"
    mybytes = parse_csv(csv_file)

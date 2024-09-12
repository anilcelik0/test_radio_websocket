from celery import shared_task
import socket
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import subprocess

@shared_task
def listen_to_port():
    channel_layer = get_channel_layer()

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect(('localhost', 8001))
        print("Listening on port 8001...")

        while True:
            try:
            # Continuously receive data and process it
                data = sock.recv(4096)  # Adjust the buffer size as needed
                if not data:
                    break
                # Send data to WebSocket clients using Django Channels
                async_to_sync(channel_layer.group_send)(
                        "audio_group",  # Group name
                        {
                            "type": "send_audio_data",  # This matches the method name in AudioStreamConsumer
                            "message": data,  # Encoded binary data as a string
                        }
                    )
            except Exception as e:
                print(f"Error: {e}")

@shared_task
def run_radio_pipeline():

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('0.0.0.0', 8001))
    server_socket.listen(1)
    
    print("Server is listening on port 8001...")

    while True:
        # Accept incoming connection
        client_socket, client_address = server_socket.accept()
        print(f"Connection established with {client_address}")

        # Create the pipeline of commands using subprocess
        try:
            rtl_sdr_command = [
                'rtl_sdr', '-s', '2400000', '-f', '156425000', '-g', '20', '-'
            ]
            csdr_commands = [
                'csdr', 'convert_u8_f'
            ]
            shift_command = [
                'csdr', 'shift_addition_cc', str((156425000 - 156775000) / 2400000)
            ]
            fir_decimate_command = [
                'csdr', 'fir_decimate_cc', '50', '0.005', 'HAMMING'
            ]
            fmdemod_command = [
                'csdr', 'fmdemod_quadri_cf'
            ]
            limit_command = [
                'csdr', 'limit_ff'
            ]
            deemphasis_command = [
                'csdr', 'deemphasis_nfm_ff', '48000'
            ]
            agc_command = [
                'csdr', 'fastagc_ff'
            ]
            convert_command = [
                'csdr', 'convert_f_s16'
            ]
            ffmpeg_command = [
                'ffmpeg', '-f', 's16le', '-ar', '48000', '-ac', '1', '-i', '-', '-f', 's16le', '-acodec', 'pcm_s16le', '-'
            ]

            # Set up the pipeline processes
            rtl_sdr_process = subprocess.Popen(rtl_sdr_command, stdout=subprocess.PIPE)
            csdr_process_1 = subprocess.Popen(csdr_commands, stdin=rtl_sdr_process.stdout, stdout=subprocess.PIPE)
            csdr_process_2 = subprocess.Popen(shift_command, stdin=csdr_process_1.stdout, stdout=subprocess.PIPE)
            csdr_process_3 = subprocess.Popen(fir_decimate_command, stdin=csdr_process_2.stdout, stdout=subprocess.PIPE)
            csdr_process_4 = subprocess.Popen(fmdemod_command, stdin=csdr_process_3.stdout, stdout=subprocess.PIPE)
            csdr_process_5 = subprocess.Popen(limit_command, stdin=csdr_process_4.stdout, stdout=subprocess.PIPE)
            csdr_process_6 = subprocess.Popen(deemphasis_command, stdin=csdr_process_5.stdout, stdout=subprocess.PIPE)
            csdr_process_7 = subprocess.Popen(agc_command, stdin=csdr_process_6.stdout, stdout=subprocess.PIPE)
            csdr_process_8 = subprocess.Popen(convert_command, stdin=csdr_process_7.stdout, stdout=subprocess.PIPE)
            ffmpeg_process = subprocess.Popen(ffmpeg_command, stdin=csdr_process_8.stdout, stdout=subprocess.PIPE)
            
            # Stream the output to the client
            while True:
                data = ffmpeg_process.stdout.read(4096)
                if not data:
                    break
                client_socket.sendall(data)

        except Exception as e:
            print(f"Error during processing: {e}")
        finally:
            client_socket.close()
            print(f"Connection closed with {client_address}")
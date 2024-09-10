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
    rtl_sdr_command = [
        "rtl_sdr", "-s", "2400000", "-f", "156425000", "-g", "20", "-"
    ]

    # csdr komutları
    csdr_convert_u8_f = ["csdr", "convert_u8_f"]
    csdr_shift_addition_cc = ["csdr", "shift_addition_cc", str((156425000 - 156775000) / 2400000)]
    csdr_fir_decimate_cc = ["csdr", "fir_decimate_cc", "50", "0.005", "HAMMING"]
    csdr_fmdemod_quadri_cf = ["csdr", "fmdemod_quadri_cf"]
    csdr_limit_ff = ["csdr", "limit_ff"]
    csdr_deemphasis_nfm_ff = ["csdr", "deemphasis_nfm_ff", "48000"]
    csdr_fastagc_ff = ["csdr", "fastagc_ff"]
    csdr_convert_f_s16 = ["csdr", "convert_f_s16"]

    # nc komutu
    nc_command = ["nc", "-l", "-p", "8001"]

    # Alt süreçleri kurarak zincirleme yapmak için subprocess.Popen kullan
    rtl_sdr_process = subprocess.Popen(rtl_sdr_command, stdout=subprocess.PIPE)
    convert_u8_f_process = subprocess.Popen(csdr_convert_u8_f, stdin=rtl_sdr_process.stdout, stdout=subprocess.PIPE)
    shift_addition_cc_process = subprocess.Popen(csdr_shift_addition_cc, stdin=convert_u8_f_process.stdout, stdout=subprocess.PIPE)
    fir_decimate_cc_process = subprocess.Popen(csdr_fir_decimate_cc, stdin=shift_addition_cc_process.stdout, stdout=subprocess.PIPE)
    fmdemod_quadri_cf_process = subprocess.Popen(csdr_fmdemod_quadri_cf, stdin=fir_decimate_cc_process.stdout, stdout=subprocess.PIPE)
    limit_ff_process = subprocess.Popen(csdr_limit_ff, stdin=fmdemod_quadri_cf_process.stdout, stdout=subprocess.PIPE)
    deemphasis_nfm_ff_process = subprocess.Popen(csdr_deemphasis_nfm_ff, stdin=limit_ff_process.stdout, stdout=subprocess.PIPE)
    fastagc_ff_process = subprocess.Popen(csdr_fastagc_ff, stdin=deemphasis_nfm_ff_process.stdout, stdout=subprocess.PIPE)
    convert_f_s16_process = subprocess.Popen(csdr_convert_f_s16, stdin=fastagc_ff_process.stdout, stdout=subprocess.PIPE)
    nc_process = subprocess.Popen(nc_command, stdin=convert_f_s16_process.stdout)

    # Son süreç olan nc_process bitene kadar bekleyin
    nc_process.wait()

    print("completed task")
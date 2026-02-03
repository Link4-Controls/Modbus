# Import Libraries
from pymodbus.client import ModbusSerialClient
import time

# Define Modbus Values
PORT = "COM10"
BAUD = 19200
DEVICE_ID = 134  # Modbus Address

client = ModbusSerialClient(
    port=PORT,
    baudrate=BAUD,
    bytesize=8,
    parity="N",
    stopbits=1,
    timeout=1.0,
)

# Define register map addresses 
HR_RELAY_CTRL = 199  # Write to relays
HR_RELAY_STATE = 210 # Relay states 
HR_DI_STATE    = 211 # Digital inputs 
HR_TEMP = 299  # Temperature register (°C * 100, 0x7FFF if not connected)
HR_HUM  = 300  # Humidity register (%RH * 100, 0xFFFF if not connected)


if not client.connect():
    raise SystemExit(f"Could not open {PORT}")
print("✓ Connected")

#Helper Functions 
def read_hr(address, count=1):
    """Read holding registers and return a list of values."""
    rr = client.read_holding_registers(address=address, count=count, device_id=DEVICE_ID)
    if rr.isError():
        raise RuntimeError(f"Read error @ HR{address}: {rr}")
    return rr.registers

def write_hr(address, value):
    """Write single holding register."""
    rq = client.write_register(address=address, value=value, device_id=DEVICE_ID)
    if rq.isError():
        raise RuntimeError(f"Write error @ HR{address}: {rq}")

def bits_lsb8(value):
    """Return 8 bits (bit0..bit7) from a byte value."""
    return [(value >> n) & 1 for n in range(8)]

def format_bits(label_prefix, value, on_name="ON", off_name="OFF"):
    """Format lower 8 bits as CH1..CH8 readable states."""
    bits = bits_lsb8(value)
    lines = [f"{label_prefix}{i+1}: {on_name if bits[i] else off_name}" for i in range(8)]
    return " | ".join(lines)

def read_temp_hum():
    t_raw = read_hr(HR_TEMP, 1)[0] # Temperature Value
    h_raw = read_hr(HR_HUM, 1)[0] # Humidity Value
    temp_connected = (t_raw != 0x7FFF)  # Validate temp sensor is connected
    hum_connected  = (h_raw != 0xFFFF)  # Validate humidity sensor is connected
    # Comptute values if sensors are connected
    temp_c = (t_raw / 100.0) if temp_connected else None 
    temp_f = (temp_c * 9/5 + 32) if temp_connected else None  
    hum    = (h_raw / 100.0) if hum_connected else None  

    return {
        "temp_connected": temp_connected,
        "hum_connected": hum_connected,
        "temp_c": temp_c,
        "temp_f": temp_f,
        "hum": hum,
        "t_raw": t_raw,
        "h_raw": h_raw,
    }

def print_temp_hum():
    # Read raw registers
    t_raw = read_hr(299, 1)[0]   # °C × 100, or 0x7FFF if sensor missing
    h_raw = read_hr(300, 1)[0]   # %RH × 100, or 0xFFFF if sensor missing

    # Temperature
    if t_raw == 0x7FFF:
        print("Temperature sensor: not connected")
    else:
        temp_c = t_raw / 100.0
        temp_f = temp_c * 9/5 + 32
        print(f"Temperature: {temp_c:.2f} °C ({temp_f:.2f} °F)")

    # Humidity
    if h_raw == 0xFFFF:
        print("Humidity sensor: not connected")
    else:
        hum = h_raw / 100.0
        print(f"Relative Humidity: {hum:.2f} % ")
        
#Project Info
project_id = read_hr(0, 1)[0]
major = read_hr(1, 1)[0]
minor = read_hr(2, 1)[0]
print(f"Project ID: {project_id}")
print(f"Firmware: {major}.{minor}")

# Read initial states
relay_state_before = read_hr(HR_RELAY_STATE, 1)[0]
di_state_before = read_hr(HR_DI_STATE, 1)[0]

# Turn on relay all relays for 5s
print("Turning ON all relays for 5s")
write_hr(HR_RELAY_CTRL, 0b11111111)
time.sleep(5)

# Read after state
relay_state_after = read_hr(HR_RELAY_STATE, 1)[0]
di_state_after = read_hr(HR_DI_STATE, 1)[0]

print(f"Relay state: {relay_state_after:08b}  "
      f"({format_bits('R', relay_state_after)})")
print(f"Digital inputs: {di_state_after:08b}  "
      f"({format_bits('DI', di_state_after)})")

# Temperature / Humidity readout
print_temp_hum()

# Turn off relays
print("Turning OFF all relays…")
write_hr(HR_RELAY_CTRL, 0x0000)
time.sleep(2)

# Exit
client.close()
print("✓ Closed")


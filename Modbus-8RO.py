from pymodbus.client import ModbusSerialClient
import time

PORT = "" # Enter your COM Port
DEVICE_ID =  # Enter your Modbus Address
BAUD = 19200   # Link4 Modules use a baudrate of 19200

client = ModbusSerialClient( port=PORT,baudrate=BAUD,bytesize=8,parity="N",stopbits=1,timeout=1.0) 

def read_hr(address, count=1):
    rr = client.read_holding_registers(address=address, count=count, device_id=DEVICE_ID)
    return rr.registers

def write_hr(address, value):
    rq = client.write_register(address=address, value=value, device_id=DEVICE_ID)

def bits_lsb8(value):
    return [(value >> n) & 1 for n in range(8)]

def format_bits(label_prefix, value, on_name="ON", off_name="OFF"):
    bits = bits_lsb8(value)
    lines = [f"{label_prefix}{i+1}: {on_name if bits[i] else off_name}" for i in range(8)]
    return " | ".join(lines)

print("✓ Connected")
print("Turning ON relay #8 for 5s")
write_hr(199, 0b10000000) # Turn ON relay #8 for 5s
time.sleep(5)

relay_state = read_hr(210, 1)[0] # Read value of the holding register
print(f"Relay state: {relay_state:08b}" f"({format_bits('R', relay_state)})")

print("Turning OFF all relays")
write_hr(199, 0x0000) # Turn OFF all relays 
time.sleep(2)
client.close()
print("✓ Closed")

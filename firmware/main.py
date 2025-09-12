import time
from machine import Pin, I2C, ADC, SoftI2C
from ssd1306 import SSD1306_I2C
import ssd1306
import dht
from bh1750 import BH1750
import dfplayermini
import urequests
import wifimgr 

plants_name = {
    "desert_cactus": {
        "soil": {"low": 3481, "high": 2457},   
        "temp": {"low": 8, "high": 38},
        "light": {"low": 800, "high": 3000}
    },
    "succulent": {
        "soil": {"low": 3276, "high": 2048},
        "temp": {"low": 10, "high": 35},
        "light": {"low": 600, "high": 2500}
    },
    "tropical_fern": {
        "soil": {"low": 2048, "high": 410},   
        "temp": {"low": 16, "high": 28},
        "light": {"low": 50, "high": 400}
    },
    "tropical_foliage": {
        "soil": {"low": 2457, "high": 819},
        "temp": {"low": 15, "high": 30},
        "light": {"low": 100, "high": 1500}
    },
    "mediterranean_herb": {
        "soil": {"low": 3071, "high": 1638},
        "temp": {"low": 12, "high": 32},
        "light": {"low": 800, "high": 2500}
    },
    "soft_herb": {
        "soil": {"low": 2662, "high": 1024},
        "temp": {"low": 14, "high": 30},
        "light": {"low": 400, "high": 1800}
    },
    "orchid": {
        "soil": {"low": 3071, "high": 1638},
        "temp": {"low": 17, "high": 29},
        "light": {"low": 200, "high": 1200}
    },
    "shade_loving": {
        "soil": {"low": 2457, "high": 819},
        "temp": {"low": 14, "high": 28},
        "light": {"low": 30, "high": 400}
    },
    "bright_flowering": {
        "soil": {"low": 2867, "high": 1229},
        "temp": {"low": 15, "high": 30},
        "light": {"low": 600, "high": 2000}
    },
    "temperate_tree": {
        "soil": {"low": 2867, "high": 1229},
        "temp": {"low": 10, "high": 30},
        "light": {"low": 300, "high": 2000}
    },
    "fruit_veg": {
        "soil": {"low": 2457, "high": 819},
        "temp": {"low": 16, "high": 33},
        "light": {"low": 1000, "high": 3000}
    },
    "bonsai": {
        "soil": {"low": 2867, "high": 1433},
        "temp": {"low": 8, "high": 28},
        "light": {"low": 500, "high": 2000}
    }
}

def get_server(url, timeout=3):
    try:
        res = urequests.get(url)
        if res.status_code != 200:
            res.close()
            return False
        response = res.json()
        res.close()
        return response
    
    except:
        return False
    
    
    


def save_new_plant(plant_id):
    with open ("last_plant.txt", "w") as file_last_plant:
        file_last_plant.write(plant_id)

def load_last_plant():
    with open ("last_plant.txt", "r") as file_last_plant:
        return file_last_plant.read().strip()
        
        
        
        
            
last_id = load_last_plant()       
wifimgr.get_connection()         

while True:
    server_response = get_server("http://192.168.0.104:5001/current_plant")
    
    if server_response:
        plant_id = server_response.get("plant_id")    
        #server = ok + new plant
        if plant_id != last_id:
            save_new_plant(plant_id)     #replace the txt by new plant
            last_id = plant_id
        #server = ok but same plant
        else:
            plant_id = last_id
            
        
    #server = off keep the last plant
    else:
        plant_id = last_id
        



    plant_feature = plants_name[plant_id]
    soil = plant_feature["soil"]
    temp = plant_feature["temp"]
    lum = plant_feature["light"]
      
    def get_hum_soil():
        
        soil_adc = ADC(Pin(34))
        soil_adc.atten(ADC.ATTN_11DB) #like change the measurement scale in esp32? (I saw it on a tutorial but I don't think I fully understand it... :(
        value = soil_adc.read()
        
        if value >= soil["low"]:
            return 0
        elif value <= soil["high"]:
            return 2
        elif soil["high"] < value < soil["low"]:    #very weird... but the data for soil is + = to dry   and   - = too wet
            return 1
        else:
            return 4       #nothing happen if the sensor break down 
        
    def get_temp():
        
        temp_sensor = dht.DHT22(Pin(4))
        temp_sensor.measure()
        value = temp_sensor.temperature()
        
        if value <= temp["low"]:
            return 0
        elif value >= temp["high"]:
            return 2
        elif temp["low"] < value < temp["high"]:
            return 1
        else:
            return 4
        
        
    def get_light():
        
        i2c = SoftI2C(scl=Pin(22), sda=Pin(21), freq=400000)
        light_sensor = BH1750(bus=i2c, addr=0x23)
        value = light_sensor.luminance(BH1750.CONT_HIRES_1)     #measurement mode
        
        if value <= lum["low"]:
            return 0
        elif value >= lum["high"]:
            return 2
        elif lum["low"] < value < lum["high"]:
            return 1
        else:
            return 4
        
    
    i2c = SoftI2C(scl=Pin(22), sda=Pin(21))
    screen = ssd1306.SSD1306_I2C(128, 64, i2c)
    
   
    state_hum = get_hum_soil()
    state_temp = get_temp()
    state_light = get_light()
    
    #send data to flask
    data = {
            "plant_id": plant_id,
            "state_hum": state_hum,
            "state_temp": state_temp,
            "state_light": state_light
            }
    try:
        urequests.post("http://192.168.0.104:5001/telemetry", json=data).close()
    except:
        pass



    if state_hum == 0:
        screen.text("dry!︎", 90, 0)
        screen.show()
       
    elif state_hum == 1:
        screen.text("︎ok", 90, 0)
        screen.show()
       
    elif state_hum == 2:
        screen.text("wet!", 90, 0)
        screen.show()
        
        
    if state_temp == 0:
        screen.text("*cold!︎", 90, 25)
        screen.show()
       
    elif state_temp == 1:
        screen.text("ok", 90, 25)
        screen.show()
       
    elif state_temp == 2:
        screen.text("hot!!", 90, 25)
        screen.show()
        
        
    if state_light == 0:
        screen.text("dark!︎", 70, 45)
        screen.show()
       
    elif state_light == 1:
        screen.text("︎ok", 70, 45)
        screen.show()
       
    elif state_light == 2:
        screen.text("bright!", 70, 45)
        screen.show()
    

  
    if state_hum == 2 or state_temp == 2 or state_light == 2 or state_hum == 0 or state_temp == 0 or state_light == 0:
        screen.text(":(", 30, 20)
        screen.text("sad!", 30, 30)
        screen.show()
   
        
    else:
        screen.text(":)", 30, 20)
        screen.text("happy!", 30, 30)
        screen.show()
           
      
    time.sleep(3)
    
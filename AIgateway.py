from keras.models import load_model
from PIL import Image, ImageOps
import numpy as np
import cv2
import time
import serial.tools.list_ports
import sys
from  Adafruit_IO import  MQTTClient

AIO_FEED_IDS = ["bbc-led", "bbc-humid", "bbc-temp", "bbc-error", "bbc_ai"]
AIO_USERNAME = "lequocanh545"
AIO_KEY = "aio_NhfX43hBiPvDOWqAkjmVSqBC6aaw"

knowledgement = ["masked", "unmasked", "Empty"]

cam = cv2.VideoCapture(0)
model = load_model('keras_model.h5')

def capture_image():
    ret, frame = cam.read()
    cv2.imwrite("img_detect.jpg", frame)

def ai_detection():
    # Create the array of the right shape to feed into the keras model
    # The 'length' or number of images you can put into the array is
    # determined by the first position in the shape tuple, in this case 1.
    data = np.ndarray(shape=(1, 224, 224, 3), dtype=np.float32)
    # Replace this with the path to your image
    image = Image.open('img_detect.jpg')
    #resize the image to a 224x224 with the same strategy as in TM2:
    #resizing the image to be at least 224x224 and then cropping from the center
    size = (224, 224)
    image = ImageOps.fit(image, size, Image.ANTIALIAS)

    #turn the image into a numpy array
    image_array = np.asarray(image)
    # Normalize the image
    normalized_image_array = (image_array.astype(np.float32) / 127.0) - 1
    # Load the image into the array
    data[0] = normalized_image_array

    # run the inference
    prediction = model.predict(data)

    a = prediction[0]
    max = a[0]
    n = len(a)
    rank = 0
    for i in range (1,n):
        if a[i] > max:
            max = a[i]
            rank = i
    print("Result: ", knowledgement[rank])
    print("sending to Adafruit ", "detection: " + knowledgement[rank])
    # if len(bbc_port) > 0:
    #     ser.write((str(vt) + "#").encode())

    client.publish("bbc_ai", "detection: " + knowledgement[rank])

def  connected(client):
    print("Ket noi thanh cong...")
    for feed in AIO_FEED_IDS:
        client.subscribe(feed)

def  subscribe(client , userdata , mid , granted_qos):
    print("Subcribe thanh cong...")

def  disconnected(client):
    print("Ngat ket noi...")
    sys.exit (1)

def  message(client , feed_id , payload):
    print("Nhan du lieu: " + payload)
    if isMicrobitConnected:
        ser.write((str(payload) + "#").encode())

client = MQTTClient(AIO_USERNAME , AIO_KEY)
client.on_connect = connected
client.on_disconnect = disconnected
client.on_message = message
client.on_subscribe = subscribe
client.connect()
client.loop_background()

def getPort():
    ports = serial.tools.list_ports.comports()
    N = len(ports)
    commPort = "None"
    for i in range(0, N):
        port = ports[i]
        strPort = str(port)
        if "USB Serial Device" in strPort:
            splitPort = strPort.split(" ")
            commPort = (splitPort[0])
        # if "com0com" in strPort:
        #     splitPort = strPort.split(" ")
        #     commPort = (splitPort[0])
    bbc_port=commPort
    return commPort

bbc_port=None
isMicrobitConnected = False
if getPort() != "None":
    ser = serial.Serial(port=getPort(), baudrate=115200)
    isMicrobitConnected = True


def processData(data):
    data = data.replace("!", "")
    data = data.replace("#", "")
    splitData = data.split(":")
    print(splitData)
    if splitData[1] == "TEMP":
        client.publish("bbc-temp", splitData[2])
    if splitData[1] == "HUMID":
        client.publish("bbc-humid", splitData[2])
    if splitData[1] == "LED":
        client.publish("bbc-led", splitData[2])
    if splitData[1] == "LIGHT":
        client.publish("bbc-light", splitData[2])
    if splitData[1] == "SMOKE":
        client.publish("bbc-smoke", splitData[2])


mess = ""
def readSerial():
    bytesToRead = ser.inWaiting()
    if (bytesToRead > 0):
        global mess
        mess = mess + ser.read(bytesToRead).decode("UTF-8")
        while ("#" in mess) and ("!" in mess):
            start = mess.find("!")
            end = mess.find("#")
            processData(mess[start:end + 1])
            if (end == len(mess)):
                mess = ""
            else:
                mess = mess[end+1:]


counter = 0
while True:
    counter = counter + 1
    if(counter > 10):
        counter = 0
        capture_image()
        ai_detection()

    if isMicrobitConnected:
        readSerial()
    time.sleep(1)
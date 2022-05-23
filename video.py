import sys
from tkinter import filedialog
from PyQt5.QtWidgets import QApplication, QMainWindow,QInputDialog,QMessageBox
from PyQt5.QtGui import QImage,QPixmap
from PyQt5.QtCore import QTimer
import cv2
import face_recognition as fr
import os
from ui_gui import *
from send_mail import *


class MainWindow(QMainWindow):

    def __init__(self):

        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)


        self.loading = False
        self.start = False
        self.send_mail = False

        #List of previously stored data
        self.encoded_data = {"Name":[],"Coords":[]}
        self.detected_people = []



        self.path = filedialog.askopenfilename()
        self.cap = cv2.VideoCapture(self.path)


        self.frame_width = int( self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.frame_height =int( self.cap.get( cv2.CAP_PROP_FRAME_HEIGHT))


        self.fourcc = cv2.VideoWriter_fourcc('X','V','I','D')


        _, self.frame1 = self.cap.read()
        _, self.frame2 = self.cap.read()

        self.ui.start_btn.clicked.connect(lambda:self.start_clicked())

        self.Update_enc()
        
        temp = ''
        with open('info.txt','r') as f:
            temp = f.read()

        self.reciever, self.sender_e, self.sender_pass = temp.split('+')

        #Run the camera 
        self.timer = QTimer()
        self.timer.timeout.connect(self.showcam)
        self.controlTimer()
    
    def start_clicked(self):
        txt = self.ui.start_btn.text()

        txt = txt.lower()
        
        if txt == 'start':
            self.ui.start_btn.setText('Stop')
            self.start = True
            self.send_mail = True
        else:
            self.ui.start_btn.setText('Start')
            self.start = False
            self.send_mail = False

    def Update_enc(self):
        """
        This section loads all existing pics from images folder in memory (RAM).
        
        It is necessary because it enhances detection and recognition speed.
        """

        self.loading = True

        i = 0

        current_folder_path = os.getcwd()
        images_folder = os.path.join(current_folder_path,'images')

        #Updating the dictionary with new face encodings
        
        self.msg("Notification", "The system will load existing data please wait and don't interact with user interface",QMessageBox.Warning)

        for name in os.listdir(images_folder):
            address2 = os.path.join(images_folder,name)
            sec_pic = cv2.imread(address2)
            sec_encoding = fr.face_encodings(sec_pic)[0]
            self.encoded_data["Name"].append(name)
            self.encoded_data["Coords"].append(sec_encoding)
            i+=1
            print("Loading "+name+"........")

        self.msg("Notification", "Data loaded successfully, you can start recognition module",QMessageBox.Information)

        self.loading = False

    def showcam(self):
        """
        This method displays frame of given camera
        
        Camera input is taken by a timer
        """
        #Getting frame from webcam
        ret, image = self.cap.read()
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        #Setting dimensions of the frame
        height, width, channel = image.shape
        step = channel * width
        qImg = QImage(image.data, width, height, step, QImage.Format_RGB888)


        #Displaying frame in window
        self.ui.cam_lbl.setPixmap(QPixmap.fromImage(qImg))
        
        if not self.start:
            return
        
        moved = False
        
        if not self.loading:
            moved = self.detect_motion()
            print(moved)
        
        if moved:
            send_mail(self.reciever, self.sender_e,self.sender_pass)
                
            names = self.recognize_img(image)

            #If it detects anyone, store their name in database 
            if names!= []:
                self.msg('Information',str(names)+' detected!',QMessageBox.Information)

    def controlTimer(self):
        """
        This method starts the timer
        """
        # Get camera input and start timer
        self.timer.start(20)
 
    def msg(self, titl,txt,icon):
        """
        This is a simple messagebox function.
        """
        
        msg = QMessageBox()
        msg.setWindowTitle(titl)
        msg.setText(txt)
        msg.setIcon(icon)
        msg.exec_()

    def recognize_img(self, main_pic):
        """
        This function takes an image and checks if it exists in database

        Database exists in the same folder called 'images'
        """

        value = ''
        counter = -1
        list_of_names = []
        target_encoding = fr.face_encodings(main_pic)


        #Declaring a dictionary to hold names and encodings of available data

        if target_encoding != []:

            for coords in self.encoded_data["Coords"]:
                result = fr.compare_faces(target_encoding, coords, tolerance=0.5)
                counter+=1
                for result_f in result:

                    if result_f:
                        value = self.encoded_data["Name"][counter]
                        value = str(value)
                        value = value.replace('.jpg','')
                        list_of_names.append(value)
                    
                    
        return(list_of_names)

    def inp_box(self,title,body):
        """
        This function gets input from a user through an input box
        """

        answer = ""
        answer, done1 = QInputDialog.getText(self, title,body)
        return answer

    def detect_motion(self):
        res = False
        diff = cv2.absdiff(self.frame1, self.frame2)
        gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (5,5), 0)
        _, thresh = cv2.threshold(blur, 20, 255, cv2.THRESH_BINARY)
        dilated = cv2.dilate(thresh, None, iterations=3)
        contours, _ = cv2.findContours(dilated, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        for contour in contours:
            (x, y, w, h) = cv2.boundingRect(contour)

            if cv2.contourArea(contour) > 900:
                res = True
                
        
        self.frame1 = self.frame2
        _, self.frame2 = self.cap.read()

        return res

if __name__ == '__main__':
    app = QApplication(sys.argv)

    # create and show mainWindow
    mainWindow = MainWindow()
    mainWindow.show()

    sys.exit(app.exec_())
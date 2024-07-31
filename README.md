In progress!!!!!!!!!!!! No code inside

Disclaimer
This software is provided "as is", without warranty of any kind. The author assumes no liability for errors or any damages resulting from the use of this software.

Callendar-Van Dusen Coefficients Calculator
This repository contains a Python program designed to calculate the coefficients of a calibrated Pt100 temperature sensor using the Callendar-Van Dusen equation. The program accepts at least three temperature and resistance values as input and outputs the corresponding coefficients.

Features
Input: Accepts a minimum of three temperature (°C) and resistance (Ω) values from a calibrated Pt100 sensor.
Output: Calculates and displays the coefficients for the Callendar-Van Dusen equation.
User-friendly command-line interface for inputting data.
Validates input data for consistency and accuracy.
Requirements
Python 3.x
NumPy

Input

![image](https://github.com/user-attachments/assets/bdb1b192-f94c-4304-af81-5b87f8199acd)

2 Probes with serialnumber,test temperature, measuring uncertainty and measured resistance of the probes.
Values of the first probe are the test values of the DKD-R- 5-6 directive table 6.3

Output

xlsx file 

![image](https://github.com/user-attachments/assets/24fe1766-feaf-4777-a0f4-e517f47e0745)

and in this case 4 jpg files.

![image](https://github.com/user-attachments/assets/fa778e67-8fd2-459f-a29c-0a82c133aa5d)




    if __name__ == "__main__":
        directory = "C:\\Test\\" 
        file_name = 'test'
        grafik_output = "C:\\Test\\Grafiken\\"
        din_class = 1                 #1 =DIN 1/3    2 = DIN A    3 = DIN B
        residuen = True
        mu_bar = True
        
        graph_allinone = True
        graph_extreme = False
        graph_singel = True
    
    
        #########################################
        #########################################
        if os.path.exists(directory+ file_name + '.xls') == 1:
            path_input = directory + file_name + r'.xls'
            print(str(path_input) +' wurde gelesen.')
        if os.path.exists(directory + file_name + '.xlsx') == 1:
            path_input = directory + file_name + r'.xlsx'
            print(str(path_input) +' wurde gelesen.')
        path_output = directory + file_name + ' coeff'+ r'.xls'
    
        df = pd.read_excel(path_input,header = None)
        #df[0] =df.astype(str)        # Serien nummer in string                   
        df.columns=['Seriennummer','Temperatur','Messunsicherheit','Widerstand']
    
        multi, results, cf,ro_norm_neg =tabel_cvd(df)
        #multi,cf,ro_norm_neg = calculation(df,path_output)
        graphen(multi,din_class,ro_norm_neg)
        cf.to_excel(path_output, index = True , sheet_name = 'sheet')
    
        print ( strftime("%H:%M:%S"),  "  Programm Ende---------------------")    



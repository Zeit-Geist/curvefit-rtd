In progress!!!!!!!!!!!! No code inside


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

![image](https://github.com/user-attachments/assets/f337e609-6c2d-43c5-a788-f6aeeb8c96fc)

Output

xlsx file 

![image](https://github.com/user-attachments/assets/62b4f017-9dc1-4ab5-abf9-f8dcae80d964)


.. code-block:: python

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

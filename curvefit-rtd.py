# %%
import os
import numpy as np
import pandas as pd
from time import strftime
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt
import matplotlib.style as style
import matplotlib.colors as mcolors
from matplotlib.backends.backend_pdf import PdfPages


###Formeln

#Zum errechnen der Koeffizienten
def pos(t, ro,a,b):
    return ro*(1 + a*t + b*(t**2) ) 

def cvd(t, ro,a,b,c):
    return ro*(1 + a*t + b*(t**2) + c*(t**3)*(t-100.00)) 

#Zum wandeln von Widerstand in Temperatur
def negtemp(r,ro,a,b,c):
    #print(r,ro,a,b,c)
    x=0.0
    z=0
    while x < 0.001 and z <40:
        t = x-((ro+ro*a*x+ro*b*x**2+ro*c*(x-100)*x**3-r)/(ro*a+ro*2*b*x+c*ro*(4*x**3-3*100*x**2)))
        x=t-x
        z=z+1
       
    return t

def postemp(r,ro,a,b):
    return -a/b/2-((((a/b)**2)/4)+((r-ro)/(ro*b)))**0.5


#Norm Koeffizienten für positeven Temperaturbereich ITS-90
    
a_norm = 3.9083e-3
b_norm = -5.775e-7
c_norm = -4.183e-12
ro_norm_neg = 0.0

#messwert = {}

#######################################################################################################
### Pandas Frame wird in  zwei Dictionarys übertragen 
#######################################################################################################

def tabel_cvd(df) :
    messwert={}
    negi=[]
    posi=[]
    neg_all = []
    pos_all = []
    sn =[]
    ro_pos = []
    a_pos = []
    b_pos =[]
    c_neg =[]
    
    def neg(t_n, c):  #, ro_pos,a_pos,b_pos
        return coeff_pos[0]*(1 + coeff_pos[1]*t_n + coeff_pos[2]*(t_n**2) + c*(t_n**3)*(t_n-100.00)) 

## es wird geprüft ob eine SerNo. schon in dem dict vorhanden ist wenn ja angehängt wenn nicht angelegt
    for index, row in df.iterrows():
        if row[0] in messwert:
            messwert[row[0]].append((row[1],row[3]))
        else:    
            messwert[row[0]] = [(row[1],row[3])]


##Müstte mal optimiert werden vieles noch aus einer alten Version aber läuft soweit.

## Messwerte werden geteilt in positive und negative (0.1K) für die Koeffizienten Formel
    for serial in messwert.keys():
    
        negi = [[werte for werte in tup] for tup in messwert[serial] if tup[0]< -0.031]
        posi = [[werte for werte in tup] for tup in messwert[serial] if tup[0]>= -0.031]                
        neg_all.append(negi)
        pos_all.append(posi)
        sn.append(serial)

        if len(negi)==1 or len(negi)==0 and len(posi) >=3:
            for wert in posi:
                t=[]
                r=[]
            for wert in posi:
                t.append(wert[0])
                r.append(wert[1]) 
            coeff_pos ,covpsos = curve_fit(pos,t,r,p0 = [1,a_norm,b_norm],maxfev = 100000)
            ro_pos.append(coeff_pos[0].tolist())
            a_pos.append(coeff_pos[1].tolist())
            b_pos.append(coeff_pos[2].tolist())    
            c_neg.append(0.0)

        else:
            def cv2(t,ro,a,b):
                return ro*(1 + a*t + b*(t**2))
            
            def cv3(t,ro,a,b,c):     
                return ro*(1 + a*t + b*(t**2) + c*(t**3)*(t-100.00)) 
            
            #Funktion zum ermitteln der Koeffizienten in einem Rutsch
            # in einer früheren Version wurden 2 sequentielle fits durchgeführt. Dies hatte den Nachteil, das R0 A und B starr waren.
            # Besser beide Funktionen in einer Verpacken welche durch einen Fitter optimiert werden.

            def combinedcv(comboData,ro,a,b,c):
                
                extract1 = comboData[:len(x1)] # positiven Werte
                extract2 = comboData[len(x1):] # negativen WErte

                result1 = cv2(extract1,ro,a, b)
                result2 = cv3(extract2,ro,a, b, c)

                return np.append(result1, result2)


        #Messwerte werden auf Variablen aufgeteilt negativ Positiv
            #print(posi)
            t=[]
            r=[]
            t_n = []
            r_n =[]
            for wert in posi:
                t.append(wert[0])
                r.append(wert[1]) 
            for negwert in negi:
                t_n.append(negwert[0])  
                r_n.append(negwert[1])   
            #print(t)
            y1 = np.array(r)
            y2 = np.array(r_n)
            comboY = np.append(y1,y2)
            x1 = np.array(t)
            x2 = np.array(t_n)
            comboX = np.append(x1,x2)


            coeff_pos, pcov = curve_fit(combinedcv, comboX, comboY,)
            ro_pos.append(coeff_pos[0].tolist())
            a_pos.append(coeff_pos[1].tolist())
            b_pos.append(coeff_pos[2].tolist())
            if coeff_pos[3] !=1.0:
                c_neg.append(coeff_pos[3].tolist())
            else:
                c_neg.append(0.0)       

    #dict ={'Seriennummer':sn, 'R0':ro_pos,'A':a_pos,'B':b_pos,'C':c_neg}    
    cf = pd.DataFrame({'Seriennummer':sn, 'R0':ro_pos,'A':a_pos,'B':b_pos,'C':c_neg})
    #cf['Seriennummer'] = cf['Seriennummer'].astype(int)
    
    results= pd.merge(df,cf, sort= True)
    cf = cf.set_index('Seriennummer')

    
###Sortieren results und indizieren /Multiindex der Tabelle zum weiterverarbeiten
    results.sort_values(by=['Seriennummer','Temperatur'],inplace=True)

    # Pt Grundwert finden 
    if 90 < ro_pos[0] < 110:
        ro_norm_neg = 100.000
    elif 480 < ro_pos[0] < 520:
        ro_norm_neg = 500.000    
    elif 900 < ro_pos[0] < 1100:
        ro_norm_neg = 1000.000  


    # Ausgabe aufarbeitung Dataframe
    for index,werte in results.iterrows():
            
            if werte['Temperatur']<-2:
                tempn =(negtemp(werte['Widerstand'],werte['R0'],werte['A'],werte['B'],werte['C']))
                results.at[index,'Tempkoff']=tempn
                tempnn =(negtemp(werte['Widerstand'],ro_norm_neg,a_norm,b_norm,c_norm))
                results.at[index,'Tempnorm']=tempnn

        
            else:
                tempp =(postemp(werte['Widerstand'],werte['R0'],werte['A'],werte['B']))
                results.at[index,'Tempkoff']=tempp
                temppn =(postemp(werte['Widerstand'],ro_norm_neg,a_norm,b_norm))
                results.at[index,'Tempnorm']=temppn
            
    results['Abwkoff']=results['Tempkoff']-results['Temperatur']
    results['Abwnorm']=results['Tempnorm']-results['Temperatur']



    multi = results.set_index(['Seriennummer'])
    multi = multi.round({'Abwkoff':4,'Abwnorm':3})
    print( strftime("%H:%M:%S"),  "  Koeffizienten wurden errechnet" )

    return multi,results, cf,ro_norm_neg
    

############################################################################################
#################################  Graphen  ################################################


def graphen(multi,din_class,ro_norm_neg):

###### Erstellt für Jeden Fühler einen extra Graphen
    if graph_singel == True:

        #Seriennummern werden vereinzelt
        merk =[]
        for ind in multi.index:
           if ind not in merk:
            merk.append(ind)

        #Für die Graphen werden die unterschiedlichen Temperaturbereiche ermittelt        
        for ser in merk:
            a= multi.loc[ser,'Temperatur']
            
            temp_min= a.min()
            temp_max= a.max()
        
            minimal_punkt = np.linspace(temp_min,0,50)
            maximal_punkt = np.linspace(0,temp_max,100)
            mitemp_matemp = np.linspace (temp_min,temp_max,150)
            
            din_aa = 0.0017 #+  0.10
            din_a  = 0.002  #+  0.15
            din_b  = 0.005  #+  0.30
     
        #Diagramm werden in Datei gespeichert
            style.use('bmh')
            plt.figure(figsize=(12, 4),dpi= 300)
            
            plt.scatter(multi.loc[ser,'Temperatur'],multi.loc[ser,'Abwnorm'],label=None,marker='o',s=1.8,color = 'black', zorder=3) #
            if cf.at[ser,'C'] == 0:               
                widaustemp=pos(mitemp_matemp,cf.at[ser,'R0'],cf.at[ser,'A'],cf.at[ser,'B'])
                plt.plot(mitemp_matemp,postemp(widaustemp,ro_norm_neg)-mitemp_matemp ,linewidth =1, label = ser,zorder=1)
                tempneg = []

            
            if cf.at[ser,'C'] != 0:
                
                wid_cov=cvd(mitemp_matemp,cf.at[ser,'R0'],cf.at[ser,'A'],cf.at[ser,'B'],cf.at[ser,'C'])
                wid_covp =pos(mitemp_matemp,cf.at[ser,'R0'],cf.at[ser,'A'],cf.at[ser,'B'])
                temp = []
                
                for idx, i in enumerate(mitemp_matemp):
                    if i < 0:
                        
                        probe_temp =negtemp(wid_cov[idx],ro_norm_neg,a_norm,b_norm,c_norm)
                        temp.append(probe_temp - i)

                    if i >=0:
                        probe_temp =postemp(wid_covp[idx],ro_norm_neg,a_norm,b_norm)
                        temp.append(probe_temp - i)
                plt.plot(mitemp_matemp,temp, linewidth =1,label = ser) #
            plt.legend(loc="upper left")        


            if din_class == 1 and temp_min >20:
                plt.fill_between(mitemp_matemp,(mitemp_matemp * din_aa+0.1),(mitemp_matemp * -din_aa-0.1),facecolor='r',alpha=0.15)
            elif din_class ==1:
                plt.fill_between(maximal_punkt,(maximal_punkt * din_aa+0.1),(maximal_punkt * -din_aa-0.1),facecolor='r',alpha=0.15)
            if din_class == 1 and temp_min <0: plt.fill_between(minimal_punkt,(-(minimal_punkt) * din_aa+0.1),(-(minimal_punkt) * -din_aa-0.1),facecolor='r',alpha=0.15)
            
            
            if din_class == 2 and temp_min >20:
                plt.fill_between(mitemp_matemp,(mitemp_matemp * din_a+0.15),(mitemp_matemp * -din_a-0.15),facecolor='r',alpha=0.15)
            elif din_class ==2:
                plt.fill_between(maximal_punkt,(maximal_punkt * din_a+0.15),(maximal_punkt * -din_a-0.15),facecolor='r',alpha=0.15)
            if din_class == 2 and temp_min <0:plt.fill_between(minimal_punkt,(-(minimal_punkt) * din_a+0.15),(-(minimal_punkt) * -din_a-0.15),facecolor='r',alpha=0.15)
            
            if din_class == 3 and temp_min >20:
                plt.fill_between(mitemp_matemp,(mitemp_matemp * din_b+0.3),(mitemp_matemp * -din_b-0.3),facecolor='r',alpha=0.15)
            elif din_class ==3:
                plt.fill_between(maximal_punkt,(maximal_punkt * din_b+0.3),(maximal_punkt * -din_b-0.3),facecolor='r',alpha=0.15)
            if din_class == 3 and temp_min <0:plt.fill_between(minimal_punkt,(-(minimal_punkt) * din_b+0.3),(-(minimal_punkt) * -din_b-0.3),facecolor='r',alpha=0.15)

            if mu_bar == True: plt.errorbar(multi.loc[ser,'Temperatur'],multi.loc[ser,'Abwnorm'],yerr=multi.loc[ser,'Messunsicherheit'], fmt='o', mfc='yellow', color='green',
                ecolor='lightblue', elinewidth=2, capsize=3)
            plt.ylabel("Abweichung in K")
            plt.xlabel("Temperatur in °C")
            plt.title('Abweichung zur DIN')  

        
            plt.title(ser)     
            plt.savefig(grafik_output + str(ser) + ".jpg")
            print ( strftime("%H:%M:%S"),  "  Einzelkennlinie "+directory + str(ser) + ".png wurde erstellt")
            plt.clf()
            plt.close('all')

###### Extreme Kennliniendruck  #####            
    if graph_extreme == True:
    
        #Seriennummern werden vereinzelt
        
        style.use('bmh')
        plt.figure(figsize=(12, 4),dpi= 600)
        
        extrem =[]
        for ind in multi.index:
            if ind not in merk:
                merk.append(ind)

    # Koeffizeinten extreme feststellen

        extrem.append   (cf['R0'].idxmax())
        extrem.append   (cf['A'].idxmax())
        extrem.append   (cf['B'].idxmax())
        extrem.append   (cf['C'].idxmax())
        extrem.append   (cf['R0'].idxmin())
        extrem.append   (cf['A'].idxmin())
        extrem.append   (cf['B'].idxmin())
        extrem.append   (cf['C'].idxmin())

            
    #Für die Graphen werden die unterschiedlichen Temperaturextreme ermittelt        
        for ser in extrem:
            a= multi.loc[ser,'Temperatur']
            temp_min= a.min()
            temp_max= a.max()
        
            minimal_punkt = np.linspace(temp_min,0,50)
            maximal_punkt = np.linspace(0,temp_max,100)
            mitemp_matemp = np.linspace (temp_min,temp_max,150)
            din_aa = 0.0017 #+  0.10
            din_a  = 0.002  #+  0.15
            din_b  = 0.005  #+  0.30
        
        
    #Diagramm werden in Datei gespeichert
            style.use('bmh')
            plt.scatter(multi.loc[ser,'Temperatur'],multi.loc[ser,'Abwnorm'],label=None,marker='o',s=1.8,color = 'black', zorder=3) #
            if cf.at[ser,'C'] == 0:               
                widaustemp=pos(mitemp_matemp,cf.at[ser,'R0'],cf.at[ser,'A'],cf.at[ser,'B'])
                plt.plot(mitemp_matemp,postemp(widaustemp,ro_norm_neg)-mitemp_matemp ,linewidth =1, label = ser,zorder=1)
                tempneg = []

            
            if cf.at[ser,'C'] != 0:
                
                wid_cov=cvd(mitemp_matemp,cf.at[ser,'R0'],cf.at[ser,'A'],cf.at[ser,'B'],cf.at[ser,'C'])
                wid_covp =pos(mitemp_matemp,cf.at[ser,'R0'],cf.at[ser,'A'],cf.at[ser,'B'])
                temp = []
                
                for idx, i in enumerate(mitemp_matemp):
                    if i < 0:
                        
                        probe_temp =negtemp(wid_cov[idx],ro_norm_neg,a_norm,b_norm,c_norm)
                        temp.append(probe_temp - i)

                    if i >=0:
                        probe_temp =postemp(wid_covp[idx],ro_norm_neg,a_norm,b_norm)
                        temp.append(probe_temp - i)
                plt.plot(mitemp_matemp,temp, linewidth =1,label = ser) #
            plt.legend(loc="upper left")        
            
            
            
            if mu_bar == True: plt.errorbar(multi.loc[ser,'Temperatur'],multi.loc[ser,'Abwnorm'],yerr=multi.loc[ser,'Messunsicherheit'], fmt='o', mfc='yellow', color='green',
                ecolor='lightblue', elinewidth=2, capsize=3)
            plt.scatter(multi.loc[ser,'Temperatur'],multi.loc[ser,'Abwnorm'])
            
        if din_class == 1 and temp_min >20:
            plt.fill_between(mitemp_matemp,(mitemp_matemp * din_aa+0.1),(mitemp_matemp * -din_aa-0.1),facecolor='r',alpha=0.15)
        elif din_class ==1:
            plt.fill_between(maximal_punkt,(maximal_punkt * din_aa+0.1),(maximal_punkt * -din_aa-0.1),facecolor='r',alpha=0.15)
        if din_class == 1 and temp_min <0: plt.fill_between(minimal_punkt,(-(minimal_punkt) * din_aa+0.1),(-(minimal_punkt) * -din_aa-0.1),facecolor='r',alpha=0.15)
        
        
        if din_class == 2 and temp_min >20:
            plt.fill_between(mitemp_matemp,(mitemp_matemp * din_a+0.15),(mitemp_matemp * -din_a-0.15),facecolor='r',alpha=0.15)
        elif din_class ==2:
            plt.fill_between(maximal_punkt,(maximal_punkt * din_a+0.15),(maximal_punkt * -din_a-0.15),facecolor='r',alpha=0.15)
        if din_class == 2 and temp_min <0:plt.fill_between(minimal_punkt,(-(minimal_punkt) * din_a+0.15),(-(minimal_punkt) * -din_a-0.15),facecolor='r',alpha=0.15)
        
        if din_class == 3 and temp_min >20:
            plt.fill_between(mitemp_matemp,(mitemp_matemp * din_b+0.3),(mitemp_matemp * -din_b-0.3),facecolor='r',alpha=0.15)
        elif din_class ==3:
            plt.fill_between(maximal_punkt,(maximal_punkt * din_b+0.3),(maximal_punkt * -din_b-0.3),facecolor='r',alpha=0.15)
        if din_class == 3 and temp_min <0:plt.fill_between(minimal_punkt,(-(minimal_punkt) * din_b+0.3),(-(minimal_punkt) * -din_b-0.3),facecolor='r',alpha=0.15)

    #    plt.title(ser)     
        plt.savefig(grafik_output+file_name+'extreme.jpg')
        print ( strftime("%H:%M:%S"),  "  Extreme Kennlinien wurden in "+directory + file_name + ".png wurde erstellt")
        plt.close()

###### Erstellt einen Graphen mit allen Kennlinien

    if graph_allinone == True:

    #Seriennummern werden vereinzelt
        merk =[]
        for ind in multi.index:
           if ind not in merk:
            merk.append(ind)

        style.use('bmh')
        plt.figure(figsize=(12, 4),dpi= 600)
    
    #Für die Graphen werden die unterschiedlichen Temperaturbereiche ermittelt        
        for ser in merk:
            a= multi.loc[ser,'Temperatur']
            
            temp_min= a.min()
            temp_max= a.max()
        
            minimal_punkt = np.linspace(temp_min,0,50)
            maximal_punkt = np.linspace(0,temp_max,100)
            mitemp_matemp = np.linspace (temp_min,temp_max,150)
            
            din_aa = 0.0017 #+  0.10
            din_a  = 0.002  #+  0.15
            din_b  = 0.005  #+  0.30
     
        #Diagramm werden in Datei gespeichert

            plt.scatter(multi.loc[ser,'Temperatur'],multi.loc[ser,'Abwnorm'],label=None,marker='o',s=1.8,color = 'black', zorder=3) #
            if cf.at[ser,'C'] == 0:               
                widaustemp=pos(mitemp_matemp,cf.at[ser,'R0'],cf.at[ser,'A'],cf.at[ser,'B'])
                plt.plot(mitemp_matemp,postemp(widaustemp,ro_norm_neg)-mitemp_matemp ,linewidth =1, label = ser,zorder=1)
                tempneg = []

            
            if cf.at[ser,'C'] != 0:
                
                wid_cov=cvd(mitemp_matemp,cf.at[ser,'R0'],cf.at[ser,'A'],cf.at[ser,'B'],cf.at[ser,'C'])
                wid_covp =pos(mitemp_matemp,cf.at[ser,'R0'],cf.at[ser,'A'],cf.at[ser,'B'])
                temp = []
                
                for idx, i in enumerate(mitemp_matemp):
                    if i < 0:
                        
                        probe_temp =negtemp(wid_cov[idx],ro_norm_neg,a_norm,b_norm,c_norm)
                        temp.append(probe_temp - i)

                    if i >=0:
                        probe_temp =postemp(wid_covp[idx],ro_norm_neg,a_norm,b_norm)

                        temp.append(probe_temp - i)
                plt.plot(mitemp_matemp,temp, linewidth =1,label = ser) #
            plt.legend(loc="upper left")        
            
            
            if mu_bar == True: plt.errorbar(multi.loc[ser,'Temperatur'],multi.loc[ser,'Abwnorm'],yerr=multi.loc[ser,'Messunsicherheit'], fmt='o', mfc='yellow', color='green',
                                            ecolor='lightblue',ms= 0.7, elinewidth=0.9, capsize=0.9)

        if din_class == 1 and temp_min >20:
            plt.fill_between(mitemp_matemp,(mitemp_matemp * din_aa+0.1),(mitemp_matemp * -din_aa-0.1),facecolor='r',alpha=0.15)
        elif din_class ==1:
            plt.fill_between(maximal_punkt,(maximal_punkt * din_aa+0.1),(maximal_punkt * -din_aa-0.1),facecolor='r',alpha=0.15)
        if din_class == 1 and temp_min <0: plt.fill_between(minimal_punkt,(-(minimal_punkt) * din_aa+0.1),(-(minimal_punkt) * -din_aa-0.1),facecolor='r',alpha=0.15)
        
        
        if din_class == 2 and temp_min >20:
            plt.fill_between(mitemp_matemp,(mitemp_matemp * din_a+0.15),(mitemp_matemp * -din_a-0.15),facecolor='r',alpha=0.15)
        elif din_class ==2:
            plt.fill_between(maximal_punkt,(maximal_punkt * din_a+0.15),(maximal_punkt * -din_a-0.15),facecolor='r',alpha=0.15)
        if din_class == 2 and temp_min <0:plt.fill_between(minimal_punkt,(-(minimal_punkt) * din_a+0.15),(-(minimal_punkt) * -din_a-0.15),facecolor='r',alpha=0.15)
        
        if din_class == 3 and temp_min >20:
            plt.fill_between(mitemp_matemp,(mitemp_matemp * din_b+0.3),(mitemp_matemp * -din_b-0.3),facecolor='r',alpha=0.15)
        elif din_class ==3:
            plt.fill_between(maximal_punkt,(maximal_punkt * din_b+0.3),(maximal_punkt * -din_b-0.3),facecolor='r',alpha=0.15)
        if din_class == 3 and temp_min <0:plt.fill_between(minimal_punkt,(-(minimal_punkt) * din_b+0.3),(-(minimal_punkt) * -din_b-0.3),facecolor='r',alpha=0.15)

      
        
        plt.ylabel("Abweichung in K")
        plt.xlabel("Temperatur in °C")
        plt.title('Abweichung zur DIN')  

        
        plt.title("Alle Kennlinien")     
        plt.savefig(grafik_output + file_name + "allinone.jpg")
        print ( strftime("%H:%M:%S"),  "  AIO Kennlinien wurden in "+directory + file_name + ".png wurde erstellt")
        plt.close()
  
    if residuen == True:
        alle = []
        for ind in cf.index:
               if ind not in alle:
                alle.append(ind)
        

    #Für die Graphen werden die unterschiedlichen Temperaturextreme ermittelt   

        style.use('bmh')
        plt.figure(figsize=(12, 4),dpi= 600) 

        for ser in alle:    

            if isinstance(ser, float):
                ser = int(ser)

            plt.scatter(multi.loc[ser,'Temperatur'],multi.loc[ser,'Abwkoff'],label = ser, s=4.2 )
            plt.legend(bbox_to_anchor=(1.005, 1.0), borderaxespad = 0.,markerscale = 2.2,loc=2,fontsize='small')     # loc=2,
            print(ser)
            print ( strftime("%H:%M:%S"), str(ser)+ "  C  Wurde integriert")
            for i, row in multi.iterrows():
                i = str(i)
                #print(i)
                plt.annotate(i,             # The label for this point    row['Medium']
                    xy=(row['Temperatur'],row['Abwkoff']), # Position of the corresponding point
                    xytext=(7, 0),     # Offset text by 7 points to the right
                    fontsize=2.2,
                    textcoords='offset points', # tell it to use offset points
                    ha='left',         # Horizontally aligned to the left
                    va='center')       # Vertical alignment is centered


        #plt.title(str(sheet)+'  Messwertabweichung zur ermittelten Kennlinie')   
        plt.xlabel("Temperatur in °C")
        plt.ylabel("Abweichung in K")

        plt.savefig(grafik_output + file_name + "abweichungen.jpg")
        #pdf.savefig()
        #plt.close()



#########################################################################################################################
#########################################################################################################################

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


##funzt nicht mit meheren sheets


# %%

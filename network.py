# -*- coding: utf-8 -*-
"""
@author: Colonetti
"""
class Hydros:
    def __init__(self):
        self.setup();
        
    def setup(self):
        self.ID = [];	
        self.Bus = [];
        self.Upriver = [];
        self.Downriver = [];
        self.Traveltime = [];
        self.Pmax = [];
        self.Pmin = [];
        self.Qmax = [];
        self.Qmin = [];
        self.Status = [];
        self.Volmin = [];
        self.Volmax = [];
        self.Smin = [];
        self.Smax = [];
        self.qmin = [];
        self.qmax = [];
        self.V0 = [];
        self.Y0 = [];
        self.Q0 = [];
        self.S0 = [];
        self.Hbmin = [];
        self.Hbmax = [];
        self.Rho = [];
        self.Type = [];
    
    def addHydro(self, newHydro):
        self.ID.append(newHydro[0]);
        self.Bus.append(int(newHydro[1]));
        self.Upriver.append(int(newHydro[2]));
        self.Downriver.append(int(newHydro[3]));
        self.Traveltime.append(float(newHydro[4]));
        self.Pmax.append(float(newHydro[5]));
        self.Pmin.append(float(newHydro[6]));
        self.Qmax.append(float(newHydro[7]));
        self.Qmin.append(float(newHydro[8]));
        self.Status.append(int(newHydro[9]));
        self.Volmin.append(float(newHydro[10]));
        self.Volmax.append(float(newHydro[11]));
        self.Smin.append(float(newHydro[12]));
        self.Smax.append(float(newHydro[13]));
        self.qmin.append(float(newHydro[14]));
        self.qmax.append(float(newHydro[15]));
        self.V0.append(float(newHydro[16]));
        self.Y0.append(float(newHydro[17]));
        self.Q0.append(float(newHydro[18]));
        self.S0.append(float(newHydro[19]));
        self.Hbmin.append(float(newHydro[20]));
        self.Hbmax.append(float(newHydro[21]));
        self.Rho.append(float(newHydro[22]));
        self.Type.append(str(newHydro[23]));
        
class LinHydros:
    def __init__(self):
        self.setup();
        
    def setup(self):
        self.C0 = [];	
        self.C1 = [];
        self.C2 = [];
        self.A0 = [];
        self.A1 = [];
        self.B0 = [];
        self.B1 = [];
        self.D0 = [];
        self.D1 = [];
                  

class Generators:
    def __init__(self):
        self.setup();
        
    def setup(self):
        self.ID = [];
        self.Bus = [];
        self.P0 = [];
        self.Q0 = [];
        self.Qmax = [];
        self.Qmin = [];
        self.Status = [];
        self.Pmax = [];
        self.Pmin = [];
        self.CostSU = [];
        self.CostSD = [];
        self.C2 = []; #Custo quadratico
        self.C1 = []; #CVU
        self.C0 = []; #Custo constante
        self.T0 = [];
        self.Uptime = [];
        self.Downtime = [];
        self.RampU = [];
        self.RampD = [];   

    def addGenerator(self, newGenerator):
        self.ID.append(newGenerator[0]);
        self.Bus.append(int(newGenerator[1]));
        self.P0.append(float(newGenerator[2]));
        self.Q0.append(float(newGenerator[3]));
        self.Qmax.append(float(newGenerator[4]));
        self.Qmin.append(float(newGenerator[5]));
        self.Status.append(int(newGenerator[6]));
        self.Pmax.append(float(newGenerator[7]));
        self.Pmin.append(float(newGenerator[8]));
        self.CostSU.append(float(newGenerator[9]));
        self.CostSD.append(float(newGenerator[10]));
        self.C2.append(float(newGenerator[11]));
        self.C1.append(float(newGenerator[12]));
        self.C0.append(float(newGenerator[13]));
        self.T0.append(int(newGenerator[14]));
        self.Uptime.append(int(newGenerator[15]));
        self.Downtime.append(int(newGenerator[16]));
        self.RampU.append(float(newGenerator[17]));
        self.RampD.append(float(newGenerator[18]));     
        
class Buses:
    def __init__(self):
        self.setup();
        
    def setup(self):
        self.ID = [];
        self.Number = [];
        self.Type = [];
        self.Pd = [];
        self.Qd = [];
        self.Gs = [];
        self.Bs = [];
        self.Area = [];
        self.Vm = [];
        self.Va = [];
        self.Vmax = [];
        self.Vmin= [];
        self.Slack = 0;
        

    def addBus(self, newBus):
        self.ID.append(newBus[0]);
        self.Number.append(int(newBus[1]));
        self.Type.append(newBus[2]);
        if (newBus[2] == "Ref"):
            self.Slack = int(newBus[1]);
        self.Pd.append(float(newBus[3]));
        self.Qd.append(float(newBus[4]));
        self.Gs.append(float(newBus[5]));
        self.Bs.append(float(newBus[6]));
        self.Area.append(int(newBus[7]));
        self.Vm.append(float(newBus[8]));
        self.Va.append(float(newBus[9]));
        self.Vmax.append(float(newBus[10]));
        self.Vmin.append(float(newBus[11]));
        

class TransmissionLines:
    def __init__(self):
        self.setup();
        
    def setup(self):
        self.ID = [];
        self.From = [];
        self.To = [];
        self.R = [];
        self.X = [];
        self.B = [];
        self.Status = [];
        self.Smax = [];
        
    def addTL(self, newTL):
        self.ID.append(newTL[0]);
        self.From.append(int(newTL[1]));
        self.To.append(int(newTL[2]));
        self.R.append(float(newTL[3]));
        self.X.append(float(newTL[4]));
        self.B.append(float(newTL[5]));
        self.Status.append(int(newTL[6]));
        self.Smax.append(float(newTL[7]));

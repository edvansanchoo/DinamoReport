# -*- coding: utf-8 -*-
"""
@author: Colonetti
"""
import csv
import numpy as np

from network import Buses
from network import TransmissionLines
from network import Generators
from network import Hydros
from network import LinHydros


class Read_LinModel:
    def __int__(self):
        self.setup()

    def setup(self):
        self.output = 'Reading'

    def read(self, filename):                
        f = open(filename, 'r');
        reader = csv.reader(f, delimiter = ';');
        row = next(reader); # goes to the first GenH
        linhydro = LinHydros();
        
        for row in reader:
            if row[0] == '<C0>':
                row = next(reader);
                row = next(reader);
                C0 = [];
                while row [0] != '</C0>':
                    temp = [];
                    for col in row:
                        if col != '':
                            temp.append(float(col));
                    C0.append(temp);
                    row = next(reader);
                linhydro.C0 = C0;

            if row[0] == '<C1>':
                row = next(reader);
                row = next(reader);
                C1 = [];
                while row [0] != '</C1>':
                    temp = [];
                    for col in row:
                        if col != '':
                            temp.append(float(col))
                    C1.append(temp);
                    row = next(reader);
                linhydro.C1 = C1;

            if row[0] == '<C2>':
                row = next(reader);
                row = next(reader);
                C2 = [];
                while row [0] != '</C2>':
                    temp = [];
                    for col in row:
                        if col != '':
                            temp.append(float(col))
                    C2.append(temp);
                    row = next(reader);
                linhydro.C2 = C2;

            if row[0] == '<A0>':
                row = next(reader);
                row = next(reader);
                A0 = [];
                while row [0] != '</A0>':
                    temp = [];
                    for col in row:
                        if col != '':
                            temp.append(float(col))
                    A0.append(temp);
                    row = next(reader);
                linhydro.A0 = A0;

            if row[0] == '<A1>':
                row = next(reader);
                row = next(reader);
                A1 = [];
                while row [0] != '</A1>':
                    temp = [];
                    for col in row:
                        if col != '':
                            temp.append(float(col))
                    A1.append(temp);
                    row = next(reader);
                linhydro.A1 = A1;

            if row[0] == '<B0>':
                row = next(reader);
                row = next(reader);
                B0 = [];
                while row [0] != '</B0>':
                    temp = [];
                    for col in row:
                        if col != '':
                            temp.append(float(col))
                    B0.append(temp);
                    row = next(reader);
                linhydro.B0 = B0;

            if row[0] == '<B1>':
                row = next(reader);
                row = next(reader);
                B1 = [];
                while row [0] != '</B1>':
                    temp = [];
                    for col in row:
                        if col != '':
                            temp.append(float(col))
                    B1.append(temp);
                    row = next(reader);
                linhydro.B1 = B1;

            if row[0] == '<D0>':
                row = next(reader);
                row = next(reader);
                D0 = [];
                while row [0] != '</D0>':
                    temp = [];
                    for col in row:
                        if col != '':
                            temp.append(float(col))
                    D0.append(temp);
                    row = next(reader);
                linhydro.D0 = D0;


            if row[0] == '<D1>':
                row = next(reader);
                row = next(reader);
                D1 = [];
                while row [0] != '</D1>':
                    temp = [];
                    for col in row:
                        if col != '':
                            temp.append(float(col))
                    D1.append(temp);
                    row = next(reader);
                linhydro.D1 = D1;



        return (linhydro);
    
class Read_Inflows:
    def __int__(self):
        self.setup()
        
    def setup(self):
        self.output = 'Reading'
    
    def read(self, filename):                
        f = open(filename, 'r');
        reader = csv.reader(f, delimiter = ';');
        
        inflows = [];
        hour = 0;

        row = next(reader);
        row = next(reader); # skip '<BEGIN>'
        row = next(reader); # skip '<INFLOWS>'
        row = next(reader); # skip the plants' names
        while not(row[0] == '<\INFLOWS>'):
            inflows.append([]);
            for col in row:
                if col != '':
                    inflows[hour].append(float(col));
            hour = hour + 1;
            row = next(reader); # go to the next bus
                    
        return (inflows);    

class Read_Network:
    def __int__(self):
        self.setup()
        
    def setup(self):
        self.output = 'Reading'
    
    def read(self, filename):                
        f = open(filename, 'r');
        reader = csv.reader(f, delimiter = ';');
        
        buses = Buses();
        hydros = Hydros();
        generators = Generators();
        transm_lines = TransmissionLines();
        SystemBase = 100; # MVA
        
        for row in reader:
            if row[0] == '<BaseMVA>':
                row = next(reader); # goes to buses' header
                row = next(reader); # goes to the first bus
                while row [0] != '</BaseMVA>':
                    # while the end of the bus data hasn't been reached
                    SystemBase = float(row[0]);
                    row = next(reader); # go to the next bus

            if row[0] == '<GenH>':
                row = next(reader); # goes to GenH' header
                row = next(reader); # goes to the first GenH
                while row [0] != '</GenH>':
                    # while the end of the GenH data hasn't been reached
                    temp = [];
                    for col in row:
                        if col != '':
                            temp.append(col)
                    hydros.addHydro(temp);
                    row = next(reader); # go to the next GenH
            
            if row[0] == '<Bus>':
                row = next(reader); # goes to buses' header
                row = next(reader); # goes to the first bus
                while row [0] != '</Bus>':
                    # while the end of the bus data hasn't been reached
                    bus = [];
                    for col in row:
                        if col != '':
                            bus.append(col)
                    buses.addBus(bus);
                    row = next(reader); # go to the next bus
                    
            if row[0] == '<Branch>':
                row = next(reader); # goes to transmission lines' header
                row = next(reader); # goes to the first transmission line
                while row [0] != '</Branch>':
                    # while the end of the transmission line data hasn't been reached
                    TL = [];
                    for col in row:
                        if col != '':
                            TL.append(col)
                    transm_lines.addTL(TL);
                    row = next(reader); # go to the next transmission line
                    
            elif row[0] == '<GenT>':
                row = next(reader);
                row = next(reader);
                while row[0] != '</GenT>':
                    generator = [];
                    for col in row:
                        if col != '':
                            generator.append(col)
                    generators.addGenerator(generator);
                    row = next(reader); # go to the next generator
                    
        return (SystemBase, buses, generators, hydros, transm_lines);
    
class Read_Load:
    def __int__(self):
        self.setup()
        
    def setup(self):
        self.output = 'Reading'
    
    def read(self, filename, SystemBase):                
        f = open(filename, 'r');
        reader = csv.reader(f, delimiter = ';');
        
        load = [];
        hour = 0;
        
        row = next(reader); # go to the next row (skip header)
        row = next(reader);          
        while not(row[0] == '</LOAD>'):
            load.append([]);
            for col in row[1:]:
                if col == 0:
                    continue
                if col != '':
                    load[hour].append(float(col));
            hour = hour + 1;
            row = next(reader); # go to the next bus
            
        self.output = 'Done reading';                     
        return (load);
    
  

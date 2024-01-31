
import math
import numpy as np
import xlsxwriter
from scipy import sparse

from read_csv import Read_Inflows, Read_Network, Read_Load, Read_LinModel

from pyscipopt import Model, quicksum

def readcsv():
    read_network = Read_Network();
    SystemBase, bus, genT, genH, lt = read_network.read('casos/network - 6-bus system.csv');

    read_inflows = Read_Inflows();
    inflows = read_inflows.read('casos/inflows - hydros - 6-bus system.csv');

    read_load = Read_Load();
    load = read_load.read('casos/load - 6-bus system.csv', SystemBase);

    read_hydros = Read_LinModel();
    linmodel = read_hydros.read('casos/hydros - 6-bus system.csv');

    return(SystemBase, bus, genT, genH, lt, inflows, load, linmodel)

def convertepu(SystemBase, bus, genT, genH, lt, load):
    for i in range(len(load)):
        for j in range(len(load[i])):
            load[i][j] /=SystemBase;
    for i in range(len(bus.Pd)):
        bus.Pd[i] /=SystemBase;
        bus.Qd[i] /=SystemBase;
        bus.Gs[i] /=SystemBase;
        bus.Bs[i] /=SystemBase;
    for i in range(len(genT.Bus)):
        genT.P0[i] /=SystemBase;
        genT.Q0[i] /=SystemBase;
        genT.Qmax[i] /=SystemBase;
        genT.Qmin[i] /=SystemBase;
        genT.Pmax[i] /=SystemBase;
        genT.Pmin[i] /=SystemBase;
        genT.C2[i] *=(SystemBase*SystemBase);
        genT.C1[i] *=SystemBase;
        genT.RampU[i] /=SystemBase;
        genT.RampD[i] /=SystemBase;
    fg = [0.1, 0.1, 0.25];
    #for i in range(len(genH.Bus)):
    #    genH.Pmax[i] = genH.Pmax[i]*fg[i]/SystemBase;
    #    genH.Pmin[i] = genH.Pmin[i]*fg[i]/SystemBase;
    #    genH.Qmax[i] = genH.Qmax[i]*fg[i]/SystemBase;
    #    genH.Qmin[i] = genH.Qmin[i]*fg[i]/SystemBase;
    for i in range(len(lt.ID)):
        lt.Smax[i] /=SystemBase;

def ucconstantes(load, genT, genH, lt, bus):
    nT = len(load)
    nG = len(genT.Bus)
    nH = len(genH.Bus)
    nL = len(lt.ID)
    nB = len(bus.ID)
    nS = 0
    nC = 0
    for i in range(len(bus.ID)):
        if (bus.Pd[i] != 0) | (bus.Qd[i] != 0):
            nC += 1
    cte = 3600*(10**-6)
    return(nT, nG, nH, nL, nB, nS, nC, cte)

def escreveExcel(m, nG, nH, nC, nT, genT, genH, S, deficit, SystemBase, objval):
    # Create an new Excel file and add a worksheet.
    workbook = xlsxwriter.Workbook('resultSCIP.xlsx')
    worksheet = workbook.add_worksheet()

    # Widen the first column to make the text clearer.
    worksheet.set_column('A:A', 20)

    # Add a bold format to use to highlight cells.
    bold = workbook.add_format({'bold': True})

    worksheet.write('A1', 'Resultados HTUC', bold)
    k=1
    for i in range(nG):
        if genT.Status[i] == 0:
            continue
        worksheet.write(k,0,genT.ID[i])
        for j in range(nT):
            worksheet.write(k,j+1,m.getVal(gt[k-1,j]))
        k += 1
    for i in range(nH):
        worksheet.write(k,0,genH.ID[i])
        worksheet.write(k+nH,0,"S_"+genH.ID[i])
        for j in range(nT):
            worksheet.write(k,j+1,m.getVal(gh[i,j]))
            worksheet.write(k+nH,j+1,m.getVal(S[i,j]))
        k += 1
    k += nH
    for i in range(nC):
        worksheet.write(k,0,"Deficit-%d"%i)
        for j in range(nT):
            worksheet.write(k,j+1,m.getVal(deficit[i,j]))
        k += 1
    worksheet.write(k+1,0,'Custo', bold)
    worksheet.write(k+1,1,objval)

    workbook.close()

def buildNetwork(bus, load, genT, genH, lt):
    nB = len(bus.ID)
    nH = len(genH.ID)
    nL = len(lt.ID)
    nG = 0
    nC = 0
    for i in range(len(bus.ID)):
        if (bus.Pd[i] != 0) | (bus.Qd[i] != 0):
            nC += 1
    for i in range(len(genT.ID)):
        if genT.Status[i] == 1:
            nG += 1
    Agt = np.zeros((nB,nG))
    k = 0
    for i in range(len(genT.ID)):
        if genT.Status[i] == 0:
            continue
        Agt[genT.Bus[i]-1][k] = 1
        k += 1
    Agh = np.zeros((nB,nH))
    for i in range(nB):
        for j in range(nH):
            if (genH.Bus[j] == i+1):
                Agh[i][j] = 1
    Al = np.zeros((nB,nC))
    k = 0
    for i in range(nB):
        if (bus.Pd[i] != 0) | (bus.Qd[i] != 0):
            Al[i][k] = 1
            k += 1
    stat = np.zeros((nL,1))
    Ys  = np.zeros((nL,2))
    Bc  = np.zeros((nL,1))
    Ytt = np.zeros((nL,2))
    Yff = np.zeros((nL,2))
    Yft = np.zeros((nL,2))
    Ytf = np.zeros((nL,2))
    Ysh = np.zeros((nB,2))
    for i in range(nL):
        stat[i] = int(lt.Status[i])
        temp = stat[i]/(lt.R[i] + 1j*lt.X[i])
        Ys[i][0] = temp.real
        Ys[i][1] = temp.imag
        Bc[i] = stat[i]*lt.B[i]
        Ytt[i][0] = Ys[i][0]
        Ytt[i][1] = Ys[i][1] + Bc[i]/2
        Yff[i][0] = Ys[i][0]
        Yff[i][1] = Ys[i][1]
        Yft[i][0] = -Ys[i][0]
        Yft[i][1] = -Ys[i][1]
        Ytf[i][0] = -Ys[i][0]
        Ytf[i][1] = -Ys[i][1]

    Yshuntreal = []; Yshuntimag = []; X = [];
    for i in range(nB):
        Ysh[i][0] = bus.Gs[i]
        Ysh[i][1] = bus.Bs[i]
        Yshuntreal.append(Ysh[i][0])
        Yshuntimag.append(Ysh[i][1])
        X.append(i)

    f = []; t = []; V = []; W = []; ft = []; Yfftreal = []; Yfftimag = [];
    Ytftreal = []; Ytftimag = []; 
    for i in range(nL):
        f.append(lt.From[i]-1)
        t.append(lt.To[i]-1)
        V.append(1)
        W.append(i)
        ft.append(f[i])
        Yfftreal.append(Yff[i][0])
        Yfftimag.append(Yff[i][1])
        Ytftreal.append(Ytf[i][0])
        Ytftimag.append(Ytf[i][1])

    Cf = sparse.coo_matrix((V,(W,f)),shape=(nL,nB))
    Ct = sparse.coo_matrix((V,(W,t)),shape=(nL,nB))

    for i in range(nL):
        W.append(W[i])
        ft.append(t[i])
        Yfftreal.append(Yft[i][0])
        Yfftimag.append(Yft[i][1])
        Ytftreal.append(Ytt[i][0])
        Ytftimag.append(Ytt[i][1])

    Yfreal = sparse.coo_matrix((Yfftreal,(W,ft)),shape=(nL,nB))
    Yfimag = sparse.coo_matrix((Yfftimag,(W,ft)),shape=(nL,nB))
    Ytreal = sparse.coo_matrix((Ytftreal,(W,ft)),shape=(nL,nB))
    Ytimag = sparse.coo_matrix((Ytftimag,(W,ft)),shape=(nL,nB))
    Yshreal = sparse.coo_matrix((Yshuntreal,(X,X)),shape=(nB,nB))
    Yshimag = sparse.coo_matrix((Yshuntimag,(X,X)),shape=(nB,nB))

    Ybusreal = Cf.transpose()*Yfreal + Ct.transpose()*Ytreal + Yshreal
    Ybusimag = Cf.transpose()*Yfimag + Ct.transpose()*Ytimag + Yshimag

    return(Agt, Agh, Al, Ybusreal, Ybusimag)

def myModel(SystemBase, bus, genT, genH, lt, load, \
            nT, nG, nH, nL, nB, nS, nC, cte):
    m = Model()
    fg = [0.1, 0.1, 0.25];

    #Define Variables
    gt,v,w,u = {},{},{},{}; k=0;
    for i in range(nG):
        if genT.Status[i] == 0:
            continue
        for j in range(nT):
            gt[k,j] = m.addVar(vtype='C', name=("P%d_"%(j+1)+genT.ID[i]), \
                               lb=0, ub=genT.Pmax[i])
        for j in range(nT):
            v[k,j] = m.addVar(vtype='B', name=("v%d_"%(j+1)+genT.ID[i]) )
        for j in range(nT):
            w[k,j] = m.addVar(vtype='B', name=("w%d_"%(j+1)+genT.ID[i]) )
        for j in range(nT):
            u[k,j] = m.addVar(vtype='B', name=("u%d_"%(j+1)+genT.ID[i]) )
        k += 1

    gh,vol,q,S = {},{},{},{}; k=0;
    for i in range(nH):
        if genH.Status[i] ==0:
            continue
        for j in range(nT):
            gh[k,j] = m.addVar(vtype='C', name=("P%d_"%(j+1)+genH.ID[i]), \
                               lb=genH.Pmin[i]*fg[i]/SystemBase, ub=genH.Pmax[i]*fg[i]/SystemBase)
        for j in range(nT):
            vol[k,j] = m.addVar(vtype='C', name=("vol%d_"%(j+1)+genH.ID[i]), \
                                lb=genH.Volmin[i], ub=genH.Volmax[i])
        for j in range(nT):
            q[k,j] = m.addVar(vtype='C', name=("q%d_"%(j+1)+genH.ID[i]), \
                              lb=genH.qmin[i], ub=genH.qmax[i])
        for j in range(nT):
            S[k,j] = m.addVar(vtype='C', name=("S%d_"%(j+1)+genH.ID[i]), \
                              lb=genH.Smin[i], ub=genH.Smax[i])
        k += 1

    theta={}; deficit={}; k=0;
    for i in range(nB):
        for j in range(nT):
            theta[k,j] = m.addVar(vtype='C', name="Theta%d_%d" \
                                  %(k+1,j+1), lb=-math.pi, ub=+math.pi);
        k += 1
    k=0
    for i in range(nC):
        for j in range(nT):
            deficit[k,j] = m.addVar(vtype='C', name="Deficit%d_%d" \
                                    %(k+1,j+1), lb=0, ub=m.infinity())
        k += 1

    #Define Constraints

    #Thermal generators constraints
    # Pmin*u <= P <= Pmax*u, Qmin*u <= Q <= Qmax*u
    k=0
    for i in range(nG):
        if genT.Status[i] == 0:
            continue
        for j in range(nT):
            m.addCons(gt[k,j] >= genT.Pmin[i]*u[k,j], "P-GenT/Limits")
            m.addCons(gt[k,j] <= genT.Pmax[i]*u[k,j], "P-GenT/Limits")
        k += 1

    # Startup e shutdown: vg,t-wg,t = ug,t-ug,t-1
    k=0
    for i in range(nG):
        if genT.Status[i] == 0:
            continue
        for j in range(nT):
            if j == 0:
                if genT.T0[i] > 0:
                    m.addCons(v[k,j] - w[k,j] == u[k,j] - 1, "Start/Shut")
                else:
                    m.addCons(v[k,j] - w[k,j] == u[k,j], "Start/Shut")
            else:
                m.addCons(v[k,j] - w[k,j] == u[k,j] - u[k,j-1], "Start/Shut")
        k += 1

    # Uptime
    k=0
    for i in range(nG):
        if genT.Status[i] == 0:
            continue
        for j in range(nT):
            if (j+1) < genT.Uptime[i]:
                m.addCons(quicksum(v[k,l] for l in range(j+1)) <= u[k,j], "Uptime")
            else:
                m.addCons(quicksum(v[k,l] for l in \
                                     range(j+1-genT.Uptime[i],j+1)) <= u[k,j], "Uptime")
        k += 1

    # Downtime
    k=0
    for i in range(nG):
        if genT.Status[i] == 0:
            continue
        for j in range(nT):
            if (j+1) < genT.Downtime[i]:
                m.addCons(quicksum(w[k,l] for l in range(j+1)) <= 1 - u[k,j], "Downtime")
            else:
                m.addCons(quicksum(w[k,l] for l in \
                                     range(j+1-genT.Uptime[i],j+1)) <= 1 - u[k,j], "Downtime")
        k += 1

    # Ramp UP
    k=0
    for i in range(nG):
        if genT.Status[i] == 0:
            continue
        for j in range(nT):
            if j == 0:
                if genT.T0[i] > 0:
                    m.addCons(gt[k,j] - genT.P0[i] <= genT.RampU[i], "RampUP")
                else:
                    m.addCons(gt[k,j] <= genT.Pmin[i]*v[k,j], "RampUP")
            else:
                m.addCons(gt[k,j] - gt[k,j-1] <= genT.RampU[i]*u[k,j] + \
                            genT.Pmin[i]*v[k,j], "RampUP")
        k += 1

    # Ramp Down
    k=0
    for i in range(nG):
        if genT.Status[i] == 0:
            continue
        for j in range(nT):
            if j == 0:
                if genT.T0[i] > 0:
                    m.addCons(genT.P0[i] - gt[k,j] <= genT.RampD[i]*u[k,j] \
                                + genT.Pmin[i]*w[k,j], "RampDown")
                else:
                    m.addCons(- gt[k,j] <= genT.RampD[i]*u[k,j] \
                                + genT.Pmin[i]*w[k,j], "RampDown")
            else:
                m.addCons(gt[k,j-1] - gt[k,j] <= genT.RampD[i]*u[k,j] \
                                + genT.Pmin[i]*w[k,j], "RampDown")
        k += 1

    #Hydro generators constraints
    #water balance
    k=0
    for i in range(nH):
        if genH.Status[i] == 0:
            continue
        for j in range(nT):
            if j == 0:
                if genH.Upriver[i] == 0:
                    m.addCons(vol[k,j] == genH.V0[i] + cte*(inflows[k][j] - q[k,j] - S[k,j]),\
                                "Water_Balance")
                else:
                     m.addCons(vol[k,j] == genH.V0[i] + \
                                 cte*(inflows[k][j] - q[k,j] - S[k,j] \
                                      + genH.Q0[genH.Upriver[i]-1] \
                                      + genH.S0[genH.Upriver[i]-1]), "Water_Balance")
            else:
                if genH.Upriver[i] == 0:
                    m.addCons(vol[k,j] == vol[k,j-1] + cte*(inflows[j][k] - q[k,j] - S[k,j]),\
                                "Water_Balance")
                else:
                    if genH.Traveltime[genH.Upriver[k]-1] >= j+1:
                        m.addCons(vol[k,j] == vol[k,j-1] + \
                                    cte*(inflows[k][j] - q[k,j] - S[k,j] + \
                                         genH.Q0[genH.Upriver[i]-1] + \
                                         genH.S0[genH.Upriver[i]-1]), "Water_Balance")
                    else:
                        m.addCons(vol[k,j] == vol[k,j-1] + \
                                    cte*(inflows[j][k] - q[k,j] - S[k,j] + \
                                         q[genH.Upriver[k]-1,j - \
                                           genH.Traveltime[genH.Upriver[k]-1]] +  \
                                         S[genH.Upriver[k]-1,j - \
                                           genH.Traveltime[genH.Upriver[k]-1]]), \
                                         "Water_Balance")

        k += 1

    #Linear Agregated Model
    for i in range(nH):
        for j in range(nT):
            m.addCons(gh[i,j] == genH.Rho[i]*q[i,j], "Hydro Generation")

    # Load Flow Constraints
    # DC Load Flow
    for j in range(nT):
        m.addCons(quicksum(gt[k,j] for k in range(int(len(gt)/nT)) ) + \
                  quicksum(gh[k,j] for k in range(int(len(gh)/nT))) + \
                  quicksum(deficit[k,j] for k in range(nC)) == \
                  quicksum(load[j][k] for k in range(int(len(load[j])/2))) \
                  ,"Economic Dispatch")

    # Agt, Agh, Al, G, B = buildNetwork(bus, load, genT, genH, lt)
    # for i in range(nB):
    #    for j in range(nT):
    #        m.addCons(quicksum(Agt[i][k]*gt[k,j] for k in range(int(len(gt)/nT))) + \
    #                    quicksum(Agh[i][k]*gh[k,j]*fg[k]/SystemBase for k in range(int(len(gh)/nT))) + \
    #                    quicksum(B[i,k]*theta[k,j] for k in range(nB)) + \
    #                    quicksum(Al[i][k]*deficit[k,j] for k in range(nC)) == \
    #                    quicksum(Al[i][k]*load[j][k] for k in range(nC)), "DC_LoadFlow" )
    
    # # DC Line Flow Limits
    # for i in range(nL):
    #    for j in range(nT):
    #        m.addCons((theta[lt.From[i]-1,j] - theta[lt.To[i]-1,j])*(B[lt.From[i]-1,lt.To[i]-1]) \
    #                    <= lt.Smax[i], "LineFlow/Limits")
    #        m.addCons((theta[lt.From[i]-1,j] - theta[lt.To[i]-1,j])*(B[lt.From[i]-1,lt.To[i]-1]) \
    #                    >= -lt.Smax[i], "LineFlow/Limits")

#     # AC Load Flow
#     aux_Theta, aux_U, aux_T={},{},{};
#     for i in range(2*nL):
#         for j in range(nT):
#             aux_Theta[i,j] = m.addVar(vtype='C', name=("delta_%d%d"%(i,j+1)), \
#                                       lb=-m.infinity(), ub=m.infinity())
#     for i in range(2*nL):
#         for j in range(nT):
#             aux_U[i,j,1] = m.addVar(vtype='B', name=("aux_U%d%d%d"%(i,j+1,1)))
#             aux_T[i,j,1] = m.addVar(vtype='C', name=("aux_T%d%d%d"%(i,j+1,1)), \
#                                     lb=-math.pi/2, ub=-math.pi/6)
#             aux_U[i,j,2] = m.addVar(vtype='B', name=("aux_U%d%d%d"%(i,j+1,1)))
#             aux_T[i,j,2] = m.addVar(vtype='C', name=("aux_T%d%d%d"%(i,j+1,1)), \
#                                     lb=-math.pi/6, ub=0)
#             aux_U[i,j,3] = m.addVar(vtype='B', name=("aux_U%d%d%d"%(i,j+1,1)))
#             aux_T[i,j,3] = m.addVar(vtype='C', name=("aux_T%d%d%d"%(i,j+1,1)), \
#                                     lb=0, ub=math.pi/6)
#             aux_U[i,j,4] = m.addVar(vtype='B', name=("aux_U%d%d%d"%(i,j+1,1)))
#             aux_T[i,j,4] = m.addVar(vtype='C', name=("aux_T%d%d%d"%(i,j+1,1)), \
#                                     lb=math.pi/6, ub=math.pi/2)

#     psin = [[6/(4*math.pi), 3/math.pi, 3/math.pi, 6/(4*math.pi)], \
#             [-0.25, 0, 0, 0.25]]
#     pcos = [[3*math.sqrt(3)/(2*math.pi), (6-3*math.sqrt(3))/math.pi, (3*math.sqrt(3)-6)/math.pi, 3*math.sqrt(3)/(2*math.pi)],\
#             [3*math.sqrt(3)/4, 1, 1, -3*math.sqrt(3)/4]]
#     Set = [];
#     for i in range(nB):
#         Set.append(i)
#     l=0; #lmax = 2*nL - 1
#     #print(len(G[0,:].data))
#     for i in range(nB):
#         Set.remove(i)
#         LSet = len(Set)
#         for j in range(nT):
#             m.addCons(quicksum(Agt[i][k]*gt[k,j] for k in range(int(len(gt)/nT))) + \
#                       quicksum(Agh[i][k]*Ngh[k,j] for k in range(int(len(gh)/nT))) - \
#                       V[i,j]**2*G[i,i] - \
#                       V[i,j]*quicksum(V[Set[m],j]*G[i,Set[m]]*quicksum(aux_Theta[n,j] for n in range(l,len(G[i,:].data)-1)) \
#                                       for m in range(LSet))

# #                        quicksum(B[i,k]*theta[k,j] for k in range(nB)) + \
# #                        quicksum(Al[i][k]*deficit[k,j] for k in range(nC)) == \
#                       == quicksum(Al[i][k]*load[j][k] for k in range(nC)), "DC_LoadFlow" )
#         Set = [];
#         for j in range(nB):
#             Set.append(j)
#         #l += len(G[i,:].data)
    

    

    # Theta_ref = 0
    k=0
    for i in range(len(bus.ID)):
        if bus.Type == 'Ref':
            k = i
    for j in range(nT):
        m.addCons(theta[k,j] == 0, "RefBus")

    # Setting Objective
    zlower = m.addVar(vtype='C', name='zlower')
    costS = [10**4, 10**4, 0]
    m.addCons(quicksum(quicksum(genT.C1[i]*gt[i,j] for j in range(nT)) \
                           for i in range(int(len(gt)/nT))) + \
              quicksum(quicksum(genT.CostSU[i]*v[i,j] for j in range(nT)) \
                           for i in range(int(len(gt)/nT))) + \
              quicksum(quicksum(genT.CostSD[i]*w[i,j] for j in range(nT)) \
                           for i in range(int(len(gt)/nT))) + \
              quicksum(quicksum(genT.C0[i]*u[i,j] for j in range(nT)) \
                           for i in range(int(len(gt)/nT))) + \
              quicksum(quicksum(costS[i]*S[i,j] for j in range(nT)) \
                           for i in range(nH)) + \
              quicksum(quicksum(10**4*SystemBase*deficit[i,j] for j in \
                                range(nT)) for i in range(nC)) \
              <= zlower)
    m.setObjective(zlower, "minimize")
    m.data = gt, gh, q, S, deficit

    return(m, gt, gh, q, S, deficit)


if __name__ == "__main__":
    
    SystemBase, bus, genT, genH, lt, inflows, load, linmodel = readcsv();
    convertepu(SystemBase, bus, genT, genH, lt, load)
    nT, nG, nH, nL, nB, nS, nC, cte = ucconstantes(load, genT, genH, lt, bus)
    # nT = 4
    m, gt, gh, q, S, deficit = myModel(SystemBase, bus, genT, genH, lt, load, \
            nT, nG, nH, nL, nB, nS, nC, cte)
    
    m.writeProblem("toy.lp")
    #model.hideOutput() # silent/verbose mode
    m.optimize()
    print("Optimal value:", m.getObjVal())
    #for i in range(int(len(gt)/nT)):
    #    for j in range(nT):
    #        print(m.getVal(gt[i,j]))
    escreveExcel(m, nG, nH, nC, nT, genT, genH, S, deficit, SystemBase, \
                 m.getObjVal())
    
